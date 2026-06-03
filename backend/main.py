
from backend.rag_pipeline import (
    process_pdf,
    ask_pdf,
    generate_quiz_from_pdf,
    get_db_stats
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
    DeleteResponse
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
@app.post("/quiz", response_model=QuizResponse)
def generate_quiz(request: QuizRequest):

    questions = generate_quiz_from_pdf(
        request.topic,
        request.document_id,
        request.num_questions
    )

    return QuizResponse(
        questions=questions
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