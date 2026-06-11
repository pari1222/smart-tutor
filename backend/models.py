
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
    document_id: str
    topic: str
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

class SummaryRequest(BaseModel):
    document_id: str
class SummaryResponse(BaseModel):
    summary: str

class Flashcard(BaseModel):
    question: str
    answer: str


class FlashcardRequest(BaseModel):
    document_id: str
    num_cards: int = 10


class FlashcardResponse(BaseModel):
    flashcards: list[Flashcard]

class NotesRequest(BaseModel):
    document_id: str
class NotesResponse(BaseModel):
    notes: str

class TopicRequest(BaseModel):
    document_id: str


class TopicResponse(BaseModel):
    topics: list[str]

class LearningPathRequest(BaseModel):
    document_id: str

class LearningPathResponse(BaseModel):
    topics: List[dict]

class ProgressResponse(BaseModel):
    session_id: str
    questions_asked: int
    documents_studied: list[str]