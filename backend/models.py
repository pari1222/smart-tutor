from pydantic import BaseModel

class AskRequest(BaseModel):
    question: str
    session_id: str

class AskResponse(BaseModel):
    answer: str

class QuizRequest(BaseModel):
    topic: str
    num_questions: int = 5

class HealthResponse(BaseModel):
    status: str