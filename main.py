"""
FastAPI backend — AI Tutor Platform
Routes:
  GET  /health
  GET  /documents/list
  DELETE /documents/{filename}
  POST /upload
  POST /ask
  POST /quiz
  DELETE /session/{session_id}
  POST /scores              — save quiz score
  GET  /scores/{student}    — get student progress
  POST /doubts              — student submits doubt
  GET  /doubts              — admin views all doubts
  POST /doubts/{id}/reply   — admin replies to doubt
  POST /exams               — admin schedules exam
  GET  /exams               — list all scheduled exams
  DELETE /exams/{id}        — admin deletes exam
"""

import os
import sys
import shutil
import logging
from pathlib import Path
from typing import List
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv(dotenv_path=Path(__file__).parent / ".env")

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from models import (
    QuestionRequest, QuizRequest,
    AnswerResponse, QuizResponse, UploadResponse, HealthResponse, MCQOption,
    QuizScoreRequest, QuizScoreEntry,
    DoubtRequest, DoubtReply, DoubtEntry,
    ExamScheduleRequest, ExamEntry,
)
from rag_pipeline import ingest_pdf, answer_question, generate_quiz, clear_memory
from utils import save_upload_file, cleanup_temp_file, validate_pdf

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PDF_STORE = Path(__file__).parent / "pdf_store"
PDF_STORE.mkdir(exist_ok=True)

app = FastAPI(title="AI Tutor API", version="3.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True,
                   allow_methods=["*"], allow_headers=["*"])
app.mount("/pdfs", StaticFiles(directory=str(PDF_STORE)), name="pdfs")

# ─────────────────────────────────────────────
# In-memory stores (replace with DB for prod)
# ─────────────────────────────────────────────
_quiz_scores: List[dict] = []          # quiz progress records
_doubts: List[dict] = []               # student doubt messages
_exams: List[dict] = []                # scheduled exam entries
_next_doubt_id = 1
_next_exam_id  = 1

# ─────────────────────────────────────────────
# Health
# ─────────────────────────────────────────────

@app.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(status="ok", message="API running")

# ─────────────────────────────────────────────
# Documents
# ─────────────────────────────────────────────

@app.get("/documents/list")
async def list_pdfs():
    files = [f.name for f in PDF_STORE.iterdir() if f.suffix.lower() == ".pdf"]
    return {"files": sorted(files)}

@app.delete("/documents/{filename}")
async def delete_pdf(filename: str):
    target = PDF_STORE / filename
    if not target.exists():
        raise HTTPException(404, "File not found")
    target.unlink()
    return {"message": f"{filename} deleted"}

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
        shutil.copy2(tmp_path, PDF_STORE / file.filename)
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        raise HTTPException(500, f"Processing failed: {str(e)}")
    finally:
        cleanup_temp_file(tmp_path)
    return UploadResponse(message="Upload successful", filename=file.filename, chunks_created=chunks)

# ─────────────────────────────────────────────
# Ask
# ─────────────────────────────────────────────

@app.post("/ask", response_model=AnswerResponse)
async def ask_question(request: QuestionRequest):
    if not request.question.strip():
        raise HTTPException(400, "Question cannot be empty")
    try:
        result = answer_question(request.question, session_id=request.session_id)
    except Exception as e:
        logger.error(f"Answer error: {e}")
        raise HTTPException(500, str(e))
    return AnswerResponse(answer=result["answer"], sources=result["sources"],
                          session_id=request.session_id)

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
        raise HTTPException(500, str(e))
    questions = []
    for q in raw:
        try:
            questions.append(MCQOption(**q))
        except Exception:
            pass
    if not questions:
        raise HTTPException(500, "No valid questions generated")
    return QuizResponse(topic=request.topic, questions=questions)

# ─────────────────────────────────────────────
# Session
# ─────────────────────────────────────────────

@app.delete("/session/{session_id}")
async def clear_session(session_id: str):
    clear_memory(session_id)
    return {"message": "Session cleared"}

# ─────────────────────────────────────────────
# Progress Tracker — Quiz Scores
# ─────────────────────────────────────────────

@app.post("/scores", response_model=QuizScoreEntry)
async def save_score(req: QuizScoreRequest):
    """Save a quiz score after a student completes a quiz."""
    pct = round((req.correct / req.total) * 100, 1)
    entry = {
        "student":   req.student,
        "topic":     req.topic,
        "correct":   req.correct,
        "total":     req.total,
        "score_pct": pct,
        "timestamp": datetime.now().isoformat(),
    }
    _quiz_scores.append(entry)
    logger.info(f"Score saved: {req.student} → {req.topic} {pct}%")
    return QuizScoreEntry(**entry)

@app.get("/scores/{student}")
async def get_scores(student: str):
    """Return all quiz scores for a given student."""
    scores = [s for s in _quiz_scores if s["student"] == student]
    return {"student": student, "scores": scores}

@app.get("/scores")
async def get_all_scores():
    """Admin: return all students' scores."""
    return {"scores": _quiz_scores}

# ─────────────────────────────────────────────
# Doubts — Student → Admin Messaging
# ─────────────────────────────────────────────

@app.post("/doubts", response_model=DoubtEntry)
async def submit_doubt(req: DoubtRequest):
    """Student submits a doubt or topic request to admin."""
    global _next_doubt_id
    entry = {
        "id":         _next_doubt_id,
        "student":    req.student,
        "topic":      req.topic or "General",
        "message":    req.message,
        "timestamp":  datetime.now().isoformat(),
        "reply":      None,
        "replied_at": None,
    }
    _doubts.append(entry)
    _next_doubt_id += 1
    logger.info(f"Doubt #{entry['id']} from {req.student}")
    return DoubtEntry(**entry)

@app.get("/doubts")
async def list_doubts():
    """Admin: list all submitted doubts."""
    return {"doubts": _doubts}

@app.get("/doubts/student/{student}")
async def student_doubts(student: str):
    """Student: list their own doubts and replies."""
    my_doubts = [d for d in _doubts if d["student"] == student]
    return {"doubts": my_doubts}

@app.post("/doubts/{doubt_id}/reply")
async def reply_doubt(doubt_id: int, req: DoubtReply):
    """Admin replies to a specific doubt."""
    for d in _doubts:
        if d["id"] == doubt_id:
            d["reply"]      = req.reply
            d["replied_at"] = datetime.now().isoformat()
            return DoubtEntry(**d)
    raise HTTPException(404, f"Doubt #{doubt_id} not found")

# ─────────────────────────────────────────────
# Exam Schedule
# ─────────────────────────────────────────────

@app.post("/exams", response_model=ExamEntry)
async def schedule_exam(req: ExamScheduleRequest):
    """Admin schedules a weekly MCQ exam for a PDF."""
    global _next_exam_id
    entry = {
        "id":           _next_exam_id,
        "pdf_filename": req.pdf_filename,
        "topic":        req.topic,
        "exam_date":    req.exam_date,
        "num_questions": req.num_questions,
        "created_at":   datetime.now().isoformat(),
    }
    _exams.append(entry)
    _next_exam_id += 1
    logger.info(f"Exam #{entry['id']} scheduled: {req.topic} on {req.exam_date}")
    return ExamEntry(**entry)

@app.get("/exams")
async def list_exams():
    """List all scheduled exams — visible to both roles."""
    return {"exams": _exams}

@app.delete("/exams/{exam_id}")
async def delete_exam(exam_id: int):
    """Admin deletes a scheduled exam."""
    global _exams
    original = len(_exams)
    _exams = [e for e in _exams if e["id"] != exam_id]
    if len(_exams) == original:
        raise HTTPException(404, f"Exam #{exam_id} not found")
    return {"message": f"Exam #{exam_id} deleted"}

# ─────────────────────────────────────────────
# Local Run
# ─────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000)
