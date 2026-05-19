"""
Pydantic models for request/response validation.
(Optimized for FastAPI + Pydantic v2)
"""

from pydantic import BaseModel, Field
from typing import List, Optional


# ─────────────────────────────────────────────
# REQUEST MODELS
# ─────────────────────────────────────────────

class QuestionRequest(BaseModel):
    """Request model for asking a question."""
    question: str = Field(..., min_length=1, description="User question")
    session_id: Optional[str] = Field(default="default")


class QuizRequest(BaseModel):
    """Request model for generating a quiz."""
    topic: str = Field(..., min_length=1)
    num_questions: int = Field(default=5, ge=1, le=20)


# ─────────────────────────────────────────────
# QUIZ MODELS
# ─────────────────────────────────────────────

class MCQOption(BaseModel):
    """A single MCQ question."""
    question: str
    options: List[str]
    answer: str


class QuizResponse(BaseModel):
    """Response model for quiz generation."""
    topic: str
    questions: List[MCQOption]


# ─────────────────────────────────────────────
# ANSWER MODEL
# ─────────────────────────────────────────────

class AnswerResponse(BaseModel):
    """Response model for answers."""
    answer: str
    sources: List[str] = Field(default_factory=list)  # ✅ FIXED
    session_id: str


# ─────────────────────────────────────────────
# UPLOAD MODEL
# ─────────────────────────────────────────────

class UploadResponse(BaseModel):
    """Response model for upload."""
    message: str
    filename: str
    chunks_created: int


# ─────────────────────────────────────────────
# HEALTH MODEL
# ─────────────────────────────────────────────

class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    message: str