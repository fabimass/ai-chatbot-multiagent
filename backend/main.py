from fastapi import FastAPI
from pydantic import BaseModel
from dotenv import load_dotenv
from retriever import Retriever
from generator import Generator

# Load environment variables
load_dotenv()

# The retriever will handle the connection with the database and retrieve the context given a query
retriever = Retriever()

# The generator produces an answer using a prompt that includes the question and the retrieved data
generator = Generator(retriever)

# Entry point to use FastAPI
app = FastAPI()

# Define body model for the http requests
class Prompt(BaseModel):
    prompt: str

# This endpoint returns the user prompt, for testing purposes
@app.get("/api/ping")
def ping():
    return "pong"

# This endpoint receives a prompt and generates a response
@app.post("/api/ask")
def generate_answer(body: Prompt):
    answer = generator.invoke(body.prompt)
    return {"question": body.prompt, "answer": answer}
