from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def home():
    return {"message": "AI Tutor Backend Running"}

@app.get("/health")
def health():
    return {"status": "Backend is healthy"}