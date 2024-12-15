from pydantic import BaseModel
from typing import TypedDict

class QuestionModel(BaseModel):
    question: str
    session_id: str

class AnswerModel(QuestionModel):
    answer: str

class FeedbackModel(AnswerModel):
    like: bool

class State(TypedDict):
    question: str
    agent_rag: str
    agent_sql: str
    answer: str