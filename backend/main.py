
from backend.rag_pipeline import (
    process_pdf,
    ask_pdf,
    generate_quiz_from_pdf,
    get_db_stats,
    summarize_document,
    generate_flashcards,
    generate_study_notes,
    extract_topics,
    generate_learning_path
)
from fastapi import FastAPI, UploadFile, File, HTTPException
from backend.models import (
    AskRequest,
    AskResponse,
    QuizRequest,
    QuizResponse,
    HealthResponse,
    UploadResponse,
    StatsResponse,
    DocumentInfoResponse,
    DeleteResponse,
    SummaryRequest,
    SummaryResponse,
    FlashcardRequest,
    FlashcardResponse,
    Flashcard,
    NotesRequest,
    NotesResponse,
    TopicResponse,
    TopicRequest,
    LearningPathRequest,
    LearningPathResponse,
    ProgressResponse

)
from backend.progress import (
    load_progress,
    save_progress
)
import shutil
import os
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from backend.metadata import (
    load_metadata,
    save_metadata
)

from datetime import datetime

load_dotenv()
APP_NAME = os.getenv("APP_NAME")
DEBUG = os.getenv("DEBUG")
API_VERSION = os.getenv("API_VERSION")

app = FastAPI(
    title=APP_NAME,
    version=API_VERSION
)
app.add_middleware(
    CORSMiddleware,

    allow_origins=["*"],

    allow_credentials=True,

    allow_methods=["*"],

    allow_headers=["*"],
)

@app.get("/")
def home():
    return {"message": "AI Tutor Backend Running"}

@app.get("/health", response_model=HealthResponse)
def health():

    return HealthResponse(
        status="Backend is healthy"
    )

@app.post("/ask", response_model=AskResponse)
def ask_question(request: AskRequest):

    result = ask_pdf(
        request.question,
        request.session_id,
        request.document_id
    )

    progress = load_progress()

    session_id = request.session_id

    if session_id not in progress:

        progress[session_id] = {
            "questions_asked": 0,
            "documents_studied": []
        }

    progress[session_id]["questions_asked"] += 1

    if request.document_id not in progress[session_id]["documents_studied"]:

        progress[session_id]["documents_studied"].append(
            request.document_id
        )

    save_progress(progress)

    return AskResponse(
        answer=result["answer"],
        source=result["source"]
    )
@app.post(
    "/upload",
    response_model=UploadResponse
)
def upload_pdf(file: UploadFile = File(...)):
    

    try:

        if not file.filename.lower().endswith(".pdf"):
            raise HTTPException(
                status_code=400,
                detail="Only PDF files are allowed"
            )
        os.makedirs("pdf_store", exist_ok=True)
        file_path = f"pdf_store/{file.filename}"

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        process_result = process_pdf(file_path)
        metadata = load_metadata()

        metadata[file.filename] = {
            "pages": process_result["pages"],
            "chunks": process_result["chunks"],
            "upload_date": str(
                datetime.now().date()
            )
        }

        save_metadata(metadata)
        print("metadata saved successfully")

        return {
            "message": "PDF uploaded successfully",
            "filename": file.filename,
        "document_id": file.filename
        }

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )
@app.get("/documents/list")
def list_documents():

    files = os.listdir("pdf_store")

    pdf_files = []

    for file in files:
        if file.endswith(".pdf"):
            pdf_files.append(file)

    return {
        "total_files": len(pdf_files),
        "documents": pdf_files
    }

@app.get("/documents/{filename}")
def get_document(filename: str):

    file_path = f"pdf_store/{filename}"

    if os.path.exists(file_path):

        return FileResponse(
            path=file_path,
            media_type='application/pdf',
            filename=filename
        )

    raise HTTPException(
    status_code=404,
    detail="File not found"
)
@app.get(
    "/documents/{filename}/info",
    response_model=DocumentInfoResponse
)
def get_document_info(
    filename: str
):

    metadata = load_metadata()

    if filename not in metadata:

        raise HTTPException(
            status_code=404,
            detail="Document not found"
        )

    return {
        "filename": filename,
        **metadata[filename]
    }
@app.delete(
    "/documents/{filename}",
    response_model=DeleteResponse
)
def delete_document(filename: str):

    file_path = f"pdf_store/{filename}"

    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=404,
            detail="Document not found"
        )

    os.remove(file_path)

    metadata = load_metadata()

    if filename in metadata:
        del metadata[filename]
        save_metadata(metadata)

    return DeleteResponse(
        message=f"{filename} deleted successfully"
    )
@app.get(
    "/stats",
    response_model=StatsResponse
)
def get_stats():

    os.makedirs("pdf_store", exist_ok=True)
    pdf_files = [
        file
        for file in os.listdir("pdf_store")
        if file.endswith(".pdf")
    ]

    stats = get_db_stats()

    return StatsResponse(
        total_documents=len(pdf_files),
        total_chunks=stats["total_chunks"]
    )
@app.post(
    "/summary",
    response_model=SummaryResponse
)
def get_summary(
    request: SummaryRequest
):

    summary = summarize_document(
        request.document_id
    )

    return SummaryResponse(
        summary=summary
    )

@app.post(
    "/flashcards",
    response_model=FlashcardResponse
)
def flashcards(
    request: FlashcardRequest
):

    cards = generate_flashcards(
        request.document_id,
        request.num_cards
    )

    return FlashcardResponse(
        flashcards=cards
    )
@app.post(
    "/notes",
    response_model=NotesResponse
)
def create_notes(
    request: NotesRequest
):

    notes = generate_study_notes(
        request.document_id
    )

    return NotesResponse(
        notes=notes
    )
@app.post(
    "/topics",
    response_model=TopicResponse
)
def get_topics(
    request: TopicRequest
):

    topics = extract_topics(
        request.document_id
    )

    return TopicResponse(
        topics=topics
    )
@app.post("/quiz", response_model=QuizResponse)
def generate_quiz(request: QuizRequest):

    questions = generate_quiz_from_pdf(
        request.topic,
        request.document_id,
        request.num_questions
    )

    print("QUIZ RESULT:", questions)

    return QuizResponse(
        questions=questions
    )
@app.post(
    "/learning-path",
    response_model=LearningPathResponse
)
def learning_path(
    request: LearningPathRequest
):

    path = generate_learning_path(
        request.document_id
    )

    return LearningPathResponse(
        topics=path
    )
@app.get(
    "/progress/{session_id}",
    response_model=ProgressResponse
)
def get_progress(session_id: str):

    progress = load_progress()

    if session_id not in progress:

        raise HTTPException(
            status_code=404,
            detail="No progress found"
        )

    return ProgressResponse(
        session_id=session_id,
        questions_asked=progress[
            session_id
        ]["questions_asked"],
        documents_studied=progress[
            session_id
        ]["documents_studied"]
    )