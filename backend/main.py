from http.client import HTTPException
import uuid
from fastapi import FastAPI, Depends
from backend.config import rag_config, sql_config
from backend.modules.models import QuestionModel, AnswerModel, FeedbackModel, State
from backend.modules.agent_rag import AgentRag
from backend.modules.agent_sql import AgentSql
from backend.modules.supervisor import Supervisor
from backend.modules.utils import get_table_client
from azure.data.tables import TableEntity
from langchain_core.runnables import RunnableLambda
from langgraph.graph import StateGraph


# Entry point to use FastAPI
app = FastAPI()

def initial_setup():
    print("Running initial setup...")

    # Agents instantiation
    agent_rag = AgentRag(rag_config)
    print(f"{rag_config['agent_name']} ready.")
    agent_sql = AgentSql(sql_config)
    print(f"{sql_config['agent_name']} ready.")
    agents = ["agent_rag", "agent_sql"]

    # Supervisor instantiation
    supervisor = Supervisor(agents)
    print("Supervisor ready.")

    # Graph instantiation
    builder = StateGraph(State)
    builder.add_node("supervisor_node", supervisor.pick_next_agent)
    builder.add_node("summarizer_node", supervisor.summarize)
    builder.add_node("rag_node", agent_rag.generate_answer)
    builder.add_node("sql_node", agent_sql.generate_answer)
    builder.add_conditional_edges(
        "supervisor_node",
        RunnableLambda(lambda inputs: inputs["next"]),  
        {"agent_rag": "rag_node", "agent_sql": "sql_node", "FINISH": "summarizer_node"}
    )
    builder.add_edge("rag_node", "supervisor_node")
    builder.add_edge("sql_node", "supervisor_node")
    builder.set_entry_point("supervisor_node")
    graph = builder.compile()
    print("Graph ready.")

    # Tables instantiation
    feedback_table = get_table_client("Feedback")
    print("Feedback table client ready.")
    history_table = get_table_client("ChatHistory")
    print("History table client ready.") 
    
    return { "graph": graph, "feedback_table": feedback_table, "history_table": history_table }

# Store initial setup in the application state during startup
@app.on_event("startup")
async def startup():
    app.state.setup = initial_setup()

# Dependency to retrieve agents and graph
def get_setup():
    return getattr(app.state, 'setup', {})


# This endpoint returns the user prompt, for testing purposes
@app.get("/api/ping")
def ping():
    return "pong"


# This endpoint receives a prompt and generates a response
@app.post("/api/ask")
def generate_answer(body: QuestionModel, setup: dict = Depends(get_setup)):
    session_id = body.session_id
    prompt = body.question
    graph = setup["graph"]

    # Retrieve conversation history or start a new one
    session_history = get_chat_history(session_id, setup)

    try:
        result = graph.invoke({ "question": prompt })
        #add_to_chat_history(AnswerModel(**{"question": prompt, "answer": answer, "session_id": session_id}))
        return {"question": prompt, "answer": result["answer"], "agents": {key: value for key, value in result.items() if key.startswith("agent_")}}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {e}")


# This endpoint receives feedback from the user
@app.post("/api/feedback")
def store_feedback(body: FeedbackModel, setup: dict = Depends(get_setup)):
    entity = TableEntity()
    entity["PartitionKey"] = "likes" if body.like else "hates"
    entity["RowKey"] = str(uuid.uuid4())
    entity["Question"] = body.question
    entity["Answer"] = body.answer
    entity["SessionId"] = body.session_id
    feedback_table = setup["feedback_table"]

    # Insert the entity into the Azure Table
    try:
        feedback_table.create_entity(entity=entity)
        return {"message": "Feedback stored successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {e}")


# This endpoint returns the number of likes and hates
@app.get("/api/feedback")
def get_feedback_count(setup: dict = Depends(get_setup)):
    feedback_table = setup["feedback_table"]
    try:
        # Query all feedback entries
        entities = list(feedback_table.query_entities(query_filter="PartitionKey eq 'likes' or PartitionKey eq 'hates'"))
        
        # Count likes and hates
        counts = {"likes": 0, "hates": 0}
        for entity in entities:
            counts[entity["PartitionKey"]] += 1
        
        return counts
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {e}")


# This endpoint returns the chat history for a given session id
@app.get("/api/history/{session_id}")
def get_chat_history(session_id, setup: dict = Depends(get_setup)):
    history_table = setup["history_table"]
    entities = history_table.query_entities(query_filter=f"PartitionKey eq '{session_id}'")

    # Sort the entities by timestamp
    sorted_entities = sorted(
            (dict(entity, Timestamp=entity.metadata["timestamp"]) for entity in entities),
            key=lambda x: x["Timestamp"]
        )
    
    # Return the latest 2 question-answer pairs
    filtered_entities = sorted_entities[-4:]

    processed_entities = [
        {**{k: v for k, v in d.items() if k != "Timestamp" and k != "RowKey" and k != "PartitionKey"}}
        for d in filtered_entities
    ]

    return processed_entities


# This endpoint adds a new chat to the chat history for a given session id
@app.post("/api/history")
def add_to_chat_history(body: AnswerModel, setup: dict = Depends(get_setup)):
    history_table = setup["history_table"]
    try:
        # Insert the entity for the user question
        user_entity = TableEntity()
        user_entity["PartitionKey"] = body.session_id
        user_entity["RowKey"] = str(uuid.uuid4())
        user_entity["role"] = "user"
        user_entity["content"] = body.question
        history_table.create_entity(entity=user_entity)

        # Insert the entity for the bot answer
        bot_entity = TableEntity()
        bot_entity["PartitionKey"] = body.session_id
        bot_entity["RowKey"] = str(uuid.uuid4())
        bot_entity["role"] = "bot"
        bot_entity["content"] = body.answer
        history_table.create_entity(entity=bot_entity)
        
        return {"message": "Chat history updated successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {e}") 


# This endpoint deletes the chat history for a given session id
@app.delete("/api/history/{session_id}")
def delete_chat_history(session_id, setup: dict = Depends(get_setup)):
    history_table = setup["history_table"]
    entities = history_table.query_entities(f"PartitionKey eq '{session_id}'")
    count = 0
    for entity in entities:
        history_table.delete_entity(
            partition_key=entity["PartitionKey"],
            row_key=entity["RowKey"]
        )
        count += 1
    return {"message": f"Deleted {count} records successfully."}