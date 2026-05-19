"""
FastAPI backend for the AI Tutor application.
Supports Admin (upload/manage PDFs) and Student (ask questions, quiz).
"""

import os
import sys
import shutil
import logging
from pathlib import Path
from typing import List

# Ensure backend directory is on sys.path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv(dotenv_path=Path(__file__).parent / ".env")

from fastapi import FastAPI, UploadFile, File, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from models import (
    QuestionRequest,
    QuizRequest,
    AnswerResponse,
    QuizResponse,
    UploadResponse,
    HealthResponse,
    MCQOption,
)

from rag_pipeline import ingest_pdf, answer_question, generate_quiz, clear_memory
from utils import save_upload_file, cleanup_temp_file, validate_pdf

# ─────────────────────────────────────────────
# Logging
# ─────────────────────────────────────────────

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────
# Storage Setup
# ─────────────────────────────────────────────

PDF_STORE = Path(__file__).parent / "pdf_store"
PDF_STORE.mkdir(exist_ok=True)

# ─────────────────────────────────────────────
# App Initialization
# ─────────────────────────────────────────────

app = FastAPI(
    title="AI Tutor API",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static route (served AFTER API routes safely)
app.mount("/pdfs", StaticFiles(directory=str(PDF_STORE)), name="pdfs")

# ─────────────────────────────────────────────
# Health Check
# ─────────────────────────────────────────────

@app.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(status="ok", message="API running")

# ─────────────────────────────────────────────
# Document Management
# ─────────────────────────────────────────────

@app.get("/documents/list")
async def list_pdfs():
    files = [f.name for f in PDF_STORE.iterdir() if f.suffix.lower() == ".pdf"]
    return {"files": sorted(files)}

@app.delete("/documents/{filename}")
async def delete_pdf(filename: str):
    target = PDF_STORE / filename

    if not target.exists():
        raise HTTPException(status_code=404, detail="File not found")

    target.unlink()
    logger.info(f"Deleted: {filename}")

    return {"message": f"{filename} deleted"}

# ─────────────────────────────────────────────
# Upload PDF
# ─────────────────────────────────────────────

@app.post("/upload", response_model=UploadResponse)
async def upload_pdf(file: UploadFile = File(...)):

    if not validate_pdf(file.filename):
        raise HTTPException(400, "Only PDF files allowed")

    file_bytes = await file.read()

    if not file_bytes:
        raise HTTPException(400, "Empty file")

    tmp_path = save_upload_file(file_bytes, file.filename)

    try:
        chunks = ingest_pdf(tmp_path, file.filename)

        # Save permanent copy
        shutil.copy2(tmp_path, PDF_STORE / file.filename)

    except Exception as e:
        logger.error(f"Upload failed: {e}")
        raise HTTPException(500, f"Processing failed: {str(e)}")

    finally:
        cleanup_temp_file(tmp_path)

    return UploadResponse(
        message="Upload successful",
        filename=file.filename,
        chunks_created=chunks
    )

# ─────────────────────────────────────────────
# Ask Question
# ─────────────────────────────────────────────

@app.post("/ask", response_model=AnswerResponse)
async def ask_question(request: QuestionRequest):

    if not request.question.strip():
        raise HTTPException(400, "Question cannot be empty")

    try:
        result = answer_question(
            request.question,
            session_id=request.session_id
        )
    except Exception as e:
        logger.error(f"Answer error: {e}")
        raise HTTPException(500, str(e))

    return AnswerResponse(
        answer=result["answer"],
        sources=result["sources"],
        session_id=request.session_id
    )

# ─────────────────────────────────────────────
# Quiz
# ─────────────────────────────────────────────

@app.post("/quiz", response_model=QuizResponse)
async def create_quiz(request: QuizRequest):

    if not request.topic.strip():
        raise HTTPException(400, "Topic required")

    try:
        raw = generate_quiz(request.topic, request.num_questions)
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        logger.error(f"Quiz error: {e}")
        raise HTTPException(500, str(e))

    questions = []
    for q in raw:
        try:
            questions.append(MCQOption(**q))
        except Exception:
            logger.warning(f"Invalid question skipped: {q}")

    if not questions:
        raise HTTPException(500, "No valid questions generated")

    return QuizResponse(
        topic=request.topic,
        questions=questions
    )

# ─────────────────────────────────────────────
# Session
# ─────────────────────────────────────────────

@app.delete("/session/{session_id}")
async def clear_session(session_id: str):
    clear_memory(session_id)
    return {"message": "Session cleared"}

# ─────────────────────────────────────────────
# Local Run
# ─────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000)