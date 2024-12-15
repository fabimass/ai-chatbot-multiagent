from pydantic import BaseModel

# Define body model for the http requests
class QuestionModel(BaseModel):
    question: str
    session_id: str

class AnswerModel(QuestionModel):
    answer: str

class FeedbackModel(AnswerModel):
    like: bool