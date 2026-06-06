# 🎓 AI Tutor Platform

An AI-powered study assistant built with RAG (Retrieval-Augmented Generation). Upload syllabus PDFs, ask questions grounded in the content, generate quizzes, track progress, and manage exam schedules — all in one place.

---

## 🧱 Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.10+ · FastAPI · Uvicorn |
| Frontend | Streamlit |
| AI Framework | LangChain 0.3+ (LCEL) |
| LLM | Google Gemini 1.5 Flash |
| Embeddings | Google Gemini `gemini-embedding-001` |
| Vector DB | ChromaDB (local persistent storage) |
| PDF Loading | `PyPDFLoader` (langchain-community) |
| Text Splitting | `RecursiveCharacterTextSplitter` |
| Charts | Pandas + Streamlit bar chart |

---

## 📁 Project Structure

```
ai_tutor/
├── backend/
│   ├── main.py
│   ├── rag_pipeline.py
│   ├── db.py
│   ├── models.py
│   ├── utils.py
│   ├── pdf_store/
│   ├── chroma_db/
│   ├── .env
│   └── requirements.txt
└── frontend/
    ├── app.py
    └── requirements.txt
```

---

## ⚙️ Prerequisites

- Python **3.10 or higher**
- A **Google AI Studio API key** (free) → [aistudio.google.com](https://aistudio.google.com)

---

## 🚀 Setup & Installation

### 1. Create a virtual environment (recommended)

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r backend/requirements.txt
pip install -r frontend/requirements.txt
```

### 3. Configure your API key

Open `backend/.env` and add your key:

```env
GOOGLE_API_KEY=AIzaSyxxxxxxxxxxxxxxxx
CHROMA_DB_PATH=./chroma_db
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
TOP_K_RESULTS=4
```

> Never commit `.env` to version control.

### 4. Start the backend

```bash
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 5. Start the frontend (new terminal)

```bash
cd ai_tutor
streamlit run frontend/app.py
```

- Frontend → **http://localhost:8501**
- Backend API → **http://localhost:8000**
- Swagger docs → **http://localhost:8000/docs**

---

## 🔑 Demo Credentials

| Role | Username | Password |
|---|---|---|
| Admin | `admin` | `admin123` |
| Student | `student` | `student123` |

---

## 👑 Admin Features

### Upload PDF
Sidebar → Upload tab → choose PDF → **Process & Upload All**. The file is chunked, embedded with Gemini, and stored in ChromaDB.

### Manage PDFs
Preview any uploaded PDF inline or delete it from the knowledge base.

### Student Doubts
View all doubt messages submitted by students. Reply inline — students see your reply immediately in their portal.

### Exam Schedule
Pick a PDF, enter a topic/unit name, choose a date, and set the number of questions. Students see a live countdown. On exam day a **Start Exam** button auto-generates the quiz.

### Student Progress
View quiz scores for all students or filter by individual. Includes avg score, best/worst topic, and a bar chart of performance over time.

---

## 🧑‍🎓 Student Features

### 💬 Ask AI Tutor
Chat with the RAG system. Answers come strictly from uploaded PDFs. If the answer isn't in the syllabus the AI says "Not in syllabus". Toggle source chunks to see exactly which passages were used.

### 🔊 Text-to-Speech
Every AI answer has a **🔊 Listen** button. Click it to have the answer read aloud using the browser's built-in Web Speech API. No extra API key needed.

### 📄 View Syllabus
Browse and read all uploaded PDFs directly in the app via an inline viewer.

### 📝 Quiz
Enter a topic in the sidebar → generate MCQ questions → answer with radio buttons → reveal answers → submit score.

### 📊 My Progress
See your quiz history: total quizzes taken, average score, best and weakest topics, a bar chart per attempt, and a per-topic average table.

### 📅 Exam Schedule
See all upcoming exams with a live countdown. Cards turn orange when ≤ 3 days away and red on exam day. On exam day click **Start Exam** to launch the quiz automatically.

### ❓ Ask Admin
Submit doubts or topic requests directly to the admin with a topic label and message. Check back for admin replies in the same tab.

---

## 🔌 API Reference

Base URL: `http://localhost:8000`

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Liveness check |
| `POST` | `/upload` | Upload & ingest PDF |
| `GET` | `/documents/list` | List uploaded PDFs |
| `DELETE` | `/documents/{filename}` | Delete a PDF |
| `POST` | `/ask` | RAG question answering |
| `POST` | `/quiz` | Generate MCQ quiz |
| `DELETE` | `/session/{id}` | Clear chat history |
| `POST` | `/scores` | Save quiz score |
| `GET` | `/scores/{student}` | Get student scores |
| `GET` | `/scores` | Get all scores (admin) |
| `POST` | `/doubts` | Submit a doubt |
| `GET` | `/doubts` | List all doubts (admin) |
| `GET` | `/doubts/student/{name}` | Student's own doubts |
| `POST` | `/doubts/{id}/reply` | Admin replies to doubt |
| `POST` | `/exams` | Schedule an exam |
| `GET` | `/exams` | List all exams |
| `DELETE` | `/exams/{id}` | Delete an exam |
| `GET` | `/pdfs/{filename}` | Serve PDF file (static) |

---

## 🏗️ Architecture

```
Browser (Streamlit :8501)
        │
        │  REST API
        ▼
FastAPI Backend (:8000)
        │
        ├── /upload ──► PyPDFLoader ──► RecursiveCharacterTextSplitter
        │                                         │
        │                              Gemini Embeddings
        │                                         │
        │                                    ChromaDB
        │
        ├── /ask ────► ChromaDB retriever (top-k chunks)
        │                    │
        │             RAG Prompt + chat history
        │                    │
        │            Gemini 1.5 Flash LLM
        │                    │
        │             answer + source chunks
        │
        ├── /quiz ───► ChromaDB retriever (top-8 chunks)
        │                    │
        │            Gemini 1.5 Flash (JSON prompt)
        │                    │
        │             MCQ questions list
        │
        ├── /scores  ──► In-memory score store
        ├── /doubts  ──► In-memory doubt store
        └── /exams   ──► In-memory exam schedule
```

---

## 🔧 Configuration

All settings in `backend/.env`:

| Variable | Default | Description |
|---|---|---|
| `GOOGLE_API_KEY` | — | Gemini API key (required) |
| `CHROMA_DB_PATH` | `./chroma_db` | Vector DB directory |
| `CHUNK_SIZE` | `1000` | Characters per text chunk |
| `CHUNK_OVERLAP` | `200` | Overlap between chunks |
| `TOP_K_RESULTS` | `4` | Chunks retrieved per question |

---

## 🐛 Troubleshooting

**Backend shows "Offline"**
Wait 3–5 seconds and refresh. To debug, run the backend manually:
```bash
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000
```

**429 RESOURCE_EXHAUSTED (Gemini quota)**
You've hit the free tier daily limit. Either wait until tomorrow or switch the model in `backend/rag_pipeline.py`:
```python
model="gemini-1.5-flash-8b"   # higher free quota
```

**Upload fails with 500**
Check that `GOOGLE_API_KEY` is set correctly in `backend/.env` and the key is valid at [aistudio.google.com](https://aistudio.google.com).

**sentence_transformers error**
Delete `backend/chroma_db/` and re-ingest your PDFs. An old DB was built with the wrong embeddings.

**TTS (Listen button) has no sound**
The browser must allow audio. Try Chrome or Edge. Some browsers block TTS on localhost — allow it in site settings.

**Quiz scores not showing in Progress tab**
You must click **"📊 Submit & Save Score"** at the bottom of the quiz before scores appear. Scores reset when the backend restarts (in-memory store).

---

## 📦 Dependencies

### Backend
```
fastapi==0.136.1
uvicorn[standard]==0.46.0
starlette==1.0.0
python-multipart==0.0.28
langchain==1.2.17
langchain-community==0.4.1
langchain-core==1.3.2
langchain-text-splitters==1.1.2
langchain-chroma==1.1.0
langchain-google-genai==4.2.2
google-genai==1.74.0
chromadb==1.5.8
pypdf==4.2.0
pydantic==2.13.3
requests==2.33.1
python-dotenv==1.0.1
```

### Frontend
```
streamlit==1.57.0
requests==2.33.1
pandas>=2.0.0
```

---

## 📄 License

MIT — free to use, modify, and distribute.
