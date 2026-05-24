from fastapi import FastAPI, UploadFile, File, HTTPException
from backend.models import (
    AskRequest,
    QuizRequest,
    QuizResponse
)
import shutil
import os
from fastapi.responses import FileResponse


app = FastAPI()


@app.get("/")
def home():
    return {"message": "AI Tutor Backend Running"}

@app.get("/health")
def health():
    return {"status": "Backend is healthy"}

@app.post("/ask")
def ask_question(request: AskRequest):

    return {
        "answer": f"You asked: {request.question}"
    }
@app.post("/upload")
def upload_pdf(file: UploadFile = File(...)):

    try:

        if not file.filename.endswith(".pdf"):

            raise HTTPException(
                status_code=400,
                detail="Only PDF files are allowed"
            )

        file_path = f"pdf_store/{file.filename}"

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        return {
            "message": "PDF uploaded successfully",
            "filename": file.filename
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

    raise HTTPException(
    status_code=404,
    detail="File not found"
)
@app.get("/documents/{filename}")
def get_document(filename: str):

    file_path = f"pdf_store/{filename}"

    if os.path.exists(file_path):

        return FileResponse(
            path=file_path,
            media_type='application/pdf',
            filename=filename
        )

    return {
        "error": "File not found"
    }
@app.post("/quiz", response_model=QuizResponse)
def generate_quiz(request: QuizRequest):

    questions = []

    for i in range(request.num_questions):

        questions.append(
            f"{i+1}. Explain {request.topic}"
        )

    return QuizResponse(
        questions=questions
    )
