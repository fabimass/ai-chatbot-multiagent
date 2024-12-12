from http.client import HTTPException
import os
import uuid
from fastapi import FastAPI
from pydantic import BaseModel
from dotenv import load_dotenv
from retriever import Retriever
from generator import Generator
from azure.data.tables import TableServiceClient, TableEntity

# Load environment variables
load_dotenv()

# The retriever will handle the connection with the database and retrieve the context given a query
retriever = Retriever()

# The generator produces an answer using a prompt that includes the question and the retrieved data
generator = Generator(retriever)

# Entry point to use FastAPI
app = FastAPI()

sessions = {}

# Set up the connection to Azure Table Storage
table_connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
table_name = "FeedbackTable"
table_service = TableServiceClient.from_connection_string(conn_str=table_connection_string)
table_client = table_service.get_table_client(table_name)

# Define body model for the http requests
class Question(BaseModel):
    question: str
    session_id: str

class Answer(Question):
    answer: str

class Feedback(Answer):
    like: bool
    session_id: None = None

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
    # Create a unique identifier for each feedback entry
    entity = TableEntity()
    entity["PartitionKey"] = "likes" if body.like else "hates"
    entity["RowKey"] = str(uuid.uuid4())
    entity["Question"] = body.question
    entity["Answer"] = body.answer

    # Insert the entity into the Azure Table
    try:
        table_client.create_entity(entity=entity)
        return {"message": "Feedback stored successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {e}")

# This endpoint returns the number of likes and hates
@app.get("/api/feedback")
async def get_feedback_count():
    try:
        # Query for "likes" entries
        likes_count = len(list(table_client.query_entities(query_filter="PartitionKey eq 'likes'")))
        
        # Query for "hates" entries
        hates_count = len(list(table_client.query_entities(query_filter="PartitionKey eq 'hates'")))

        return {"likes": likes_count, "hates": hates_count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {e}")
    
# This endpoint returns the chat history for a given session id
@app.get("/api/history/{session_id}")
def get_chat_history(session_id):
    # Return the latest 2 question-answer pairs
    session_history = sessions.get(session_id, [])[-4:]
    return session_history

# This endpoint adds a new chat to the chat history for a given session id
@app.post("/api/history")
def add_to_chat_history(body: Answer):
    session_history = get_chat_history(body.session_id)
    session_history.append({"role": "user", "content": body.question})
    session_history.append({"role": "bot", "content": body.answer})
    sessions[body.session_id] = session_history
    return {"message": "Chat history updated successfully."}

# This endpoint deletes the chat history for a given session id
@app.delete("/api/history/{session_id}")
def delete_chat_history(session_id):
    sessions[session_id] = []
    return {"message": "Chat history deleted successfully."}