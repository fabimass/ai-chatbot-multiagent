from http.client import HTTPException
import uuid
from fastapi import FastAPI
from dotenv import load_dotenv
from retriever import Retriever
from generator import Generator
from utils import Question, Answer, Feedback, get_table_client
from azure.data.tables import TableEntity

# Load environment variables
load_dotenv()

# The retriever will handle the connection with the database and retrieve the context given a query
retriever = Retriever()

# The generator produces an answer using a prompt that includes the question and the retrieved data
generator = Generator(retriever)

# Entry point to use FastAPI
app = FastAPI()

# Clients for Azure Storage Tables
feedback_client = get_table_client("Feedback")
history_client = get_table_client("ChatHistory") 

# This endpoint returns the user prompt, for testing purposes
@app.get("/api/ping")
def ping():
    return "pong"

# This endpoint receives a prompt and generates a response
@app.post("/api/ask")
def generate_answer(body: Question):
    session_id = body.session_id
    prompt = body.question

    # Retrieve conversation history or start a new one
    session_history = get_chat_history(session_id)

    try:
        answer = generator.invoke(prompt, session_history)
        add_to_chat_history(Answer(**{"question": prompt, "answer": answer, "session_id": session_id}))
        return {"question": prompt, "answer": answer}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {e}")

# This endpoint receives feedback from the user
@app.post("/api/feedback")
async def store_feedback(body: Feedback):
    entity = TableEntity()
    entity["PartitionKey"] = "likes" if body.like else "hates"
    entity["RowKey"] = body.session_id
    entity["Question"] = body.question
    entity["Answer"] = body.answer

    # Insert the entity into the Azure Table
    try:
        feedback_client.create_entity(entity=entity)
        return {"message": "Feedback stored successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {e}")

# This endpoint returns the number of likes and hates
@app.get("/api/feedback")
async def get_feedback_count():
    try:
        # Query for "likes" entries
        likes_count = len(list(feedback_client.query_entities(query_filter="PartitionKey eq 'likes'")))
        
        # Query for "hates" entries
        hates_count = len(list(feedback_client.query_entities(query_filter="PartitionKey eq 'hates'")))

        return {"likes": likes_count, "hates": hates_count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {e}")
    
# This endpoint returns the chat history for a given session id
@app.get("/api/history/{session_id}")
def get_chat_history(session_id):
    entities = history_client.query_entities(query_filter=f"PartitionKey eq '{session_id}'")
    sorted_entities = sorted(
            (dict(entity, Timestamp=entity.metadata["timestamp"]) for entity in entities),
            key=lambda x: x["Timestamp"]
        )
    # Return the latest 2 question-answer pairs
    return sorted_entities[-4:]

# This endpoint adds a new chat to the chat history for a given session id
@app.post("/api/history")
def add_to_chat_history(body: Answer):
    try:
        # Insert the entity for the user question
        user_entity = TableEntity()
        user_entity["PartitionKey"] = body.session_id
        user_entity["RowKey"] = "user"
        user_entity["content"] = body.question
        history_client.create_entity(entity=user_entity)

        # Insert the entity for the bot answer
        bot_entity = TableEntity()
        bot_entity["PartitionKey"] = body.session_id
        bot_entity["RowKey"] = "bot"
        bot_entity["content"] = body.answer
        history_client.create_entity(entity=bot_entity)
        
        return {"message": "Chat history updated successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {e}") 

# This endpoint deletes the chat history for a given session id
@app.delete("/api/history/{session_id}")
def delete_chat_history(session_id):
    entities = history_client.query_entities(f"PartitionKey eq '{session_id}'")
    count = 0
    for entity in entities:
        history_client.delete_entity(
            partition_key=entity["PartitionKey"],
            row_key=entity["RowKey"]
        )
        count += 1
    return {"message": f"Deleted {count} records successfully."}