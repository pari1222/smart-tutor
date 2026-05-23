from fastapi import FastAPI,UploadFile, File
from backend.models import AskRequest
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

    file_path = f"pdf_store/{file.filename}"

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return {
        "message": "PDF uploaded successfully",
        "filename": file.filename
    }
@app.get("/documents/list")
def list_documents():

    files = os.listdir("pdf_store")

    pdf_files = []

    for file in files:
        if file.endswith(".pdf"):
            pdf_files.append(file)

    return {
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

    return {
        "error": "File not found"
    }