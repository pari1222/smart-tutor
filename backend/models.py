from pydantic import BaseModel
from typing import Optional,List


class AskRequest(BaseModel):
    question: str
    session_id: str
    document_id: str

class AskResponse(BaseModel):
    answer: str
    source: Optional[str] = None

class QuizRequest(BaseModel):
    topic: str
    document_id: str
    num_questions: int = 5

class HealthResponse(BaseModel):
    status: str

class QuizResponse(BaseModel):
    questions: list[str]
# upload response
class UploadResponse(BaseModel):
    message: str
    filename: str
    document_id: str
class DocumentInfoResponse(BaseModel):
    filename: str
    pages: int
    chunks: int
    upload_date: str
class StatsResponse(BaseModel):
    total_documents: int
    total_chunks: int

class DeleteResponse(BaseModel):
    message: str

