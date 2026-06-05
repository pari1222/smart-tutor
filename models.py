"""
Pydantic models for request/response validation.
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


# ─────────────────────────────────────────────
# REQUEST MODELS
# ─────────────────────────────────────────────

class QuestionRequest(BaseModel):
    question: str = Field(..., min_length=1)
    session_id: Optional[str] = Field(default="default")


class QuizRequest(BaseModel):
    topic: str = Field(..., min_length=1)
    num_questions: int = Field(default=5, ge=1, le=20)


# ─────────────────────────────────────────────
# QUIZ MODELS
# ─────────────────────────────────────────────

class MCQOption(BaseModel):
    question: str
    options: List[str]
    answer: str


class QuizResponse(BaseModel):
    topic: str
    questions: List[MCQOption]


# ─────────────────────────────────────────────
# QUIZ SCORE MODELS  (Progress Tracker)
# ─────────────────────────────────────────────

class QuizScoreRequest(BaseModel):
    student: str = Field(..., description="Student username")
    topic: str
    correct: int = Field(..., ge=0)
    total: int = Field(..., ge=1)
    session_id: str


class QuizScoreEntry(BaseModel):
    student: str
    topic: str
    correct: int
    total: int
    score_pct: float
    timestamp: str


# ─────────────────────────────────────────────
# ANSWER MODEL
# ─────────────────────────────────────────────

class AnswerResponse(BaseModel):
    answer: str
    sources: List[str] = Field(default_factory=list)
    session_id: str


# ─────────────────────────────────────────────
# UPLOAD MODEL
# ─────────────────────────────────────────────

class UploadResponse(BaseModel):
    message: str
    filename: str
    chunks_created: int


# ─────────────────────────────────────────────
# HEALTH MODEL
# ─────────────────────────────────────────────

class HealthResponse(BaseModel):
    status: str
    message: str


# ─────────────────────────────────────────────
# DOUBT MODELS  (Student → Admin messaging)
# ─────────────────────────────────────────────

class DoubtRequest(BaseModel):
    student: str = Field(..., description="Student username")
    message: str = Field(..., min_length=1)
    topic: Optional[str] = Field(default="General")


class DoubtReply(BaseModel):
    doubt_id: int
    reply: str


class DoubtEntry(BaseModel):
    id: int
    student: str
    topic: str
    message: str
    timestamp: str
    reply: Optional[str] = None
    replied_at: Optional[str] = None


# ─────────────────────────────────────────────
# EXAM SCHEDULE MODELS
# ─────────────────────────────────────────────

class ExamScheduleRequest(BaseModel):
    pdf_filename: str
    exam_date: str = Field(..., description="ISO date string YYYY-MM-DD")
    topic: str = Field(..., description="Exam topic / unit name")
    num_questions: int = Field(default=10, ge=3, le=20)


class ExamEntry(BaseModel):
    id: int
    pdf_filename: str
    topic: str
    exam_date: str
    num_questions: int
    created_at: str
