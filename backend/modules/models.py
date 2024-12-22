from pydantic import BaseModel
from typing import TypedDict

class QuestionModel(BaseModel):
    question: str
    session_id: str

class AnswerModel(QuestionModel):
    answer: str
    agents: dict

class FeedbackModel(AnswerModel):
    like: bool
    agents: None = None

class State(TypedDict):
    question: str
    agents: dict
    answer: str
    history: list