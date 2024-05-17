from fastapi import FastAPI
from pydantic import BaseModel
from dotenv import load_dotenv
from langchain import HuggingFaceHub

# Load environment variables
load_dotenv()

# Entry point to use FastAPI
app = FastAPI()

# Define body model for the http requests
class Prompt(BaseModel):
    prompt: str

# Instantiate a pre-trained Large Language Model from Hugging Face
llm = HuggingFaceHub(repo_id="google/flan-t5-large", model_kwargs={"temperature": 0.6})


# This endpoint returns the user prompt, for testing purposes
@app.post("/api/echo")
def echo(body: Prompt):
    return {"echo": body.prompt}

# This endpoint receives a prompt and generates a response
@app.post("/api/ask")
def generate_answer(body: Prompt):
    answer = llm.predict(body.prompt)
    return {"question": body.prompt, "answer": answer}
