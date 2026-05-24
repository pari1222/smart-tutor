from pydantic import BaseModel
from typing import Optional,List

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

class QuizResponse(BaseModel):
    questions: List[dict]

class QuizResponse(BaseModel):
    questions: list[str]
# upload response
class UploadResponse(BaseModel):
    message: str
    filename: str
    document_id: str

