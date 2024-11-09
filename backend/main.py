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
#retriever = Retriever()

# The generator produces an answer using a prompt that includes the question and the retrieved data
#generator = Generator(retriever)

# Entry point to use FastAPI
app = FastAPI()

# Set up the connection to Azure Table Storage
table_connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
table_name = "FeedbackTable"
table_service = TableServiceClient.from_connection_string(conn_str=table_connection_string)
table_client = table_service.get_table_client(table_name)

# Define body model for the http requests
class Prompt(BaseModel):
    prompt: str

class Feedback(BaseModel):
    question: str
    answer: str
    like: bool

# This endpoint returns the user prompt, for testing purposes
@app.get("/api/ping")
def ping():
    return "pong"

# This endpoint receives a prompt and generates a response
#@app.post("/api/ask")
#def generate_answer(body: Prompt):
#    answer = generator.invoke(body.prompt)
#    return {"question": body.prompt, "answer": answer}

# This endpoint receives feedback from the user
@app.post("/api/feedback")
async def receive_feedback(feedback: Feedback):
    # Create a unique identifier for each feedback entry
    entity = TableEntity()
    entity["PartitionKey"] = "likes" if feedback.like else "hates"
    entity["RowKey"] = str(uuid.uuid4())
    entity["Question"] = feedback.question
    entity["Answer"] = feedback.answer

    # Insert the entity into the Azure Table
    try:
        table_client.create_entity(entity=entity)
        return {"message": "Feedback stored successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error storing feedback: {e}")