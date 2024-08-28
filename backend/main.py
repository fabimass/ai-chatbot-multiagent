from fastapi import FastAPI
from pydantic import BaseModel
from dotenv import load_dotenv
from langchain_openai import AzureChatOpenAI
from retriever import Retriever

# Load environment variables
load_dotenv()

# The retriever will handle the connection with the database and retrieve the context
retriever = Retriever()



# Entry point to use FastAPI
app = FastAPI()

# Define body model for the http requests
class Prompt(BaseModel):
    prompt: str

# This endpoint returns the user prompt, for testing purposes
@app.post("/api/echo")
def echo(body: Prompt):
    return {"echo": body.prompt}

# This endpoint receives a prompt and generates a response
@app.post("/api/ask")
def generate_answer(body: Prompt):
    answer = retriever.invoke(body.prompt)
    #answer = rag_chain.invoke({"input": body.prompt})
    return {"question": body.prompt, "answer": answer}
