# 🎓 AI Tutor — Generative AI Tutoring System

An AI-powered tutoring application that answers student questions **strictly based on uploaded syllabus PDFs**, using Retrieval-Augmented Generation (RAG) to prevent hallucination.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python + FastAPI |
| Frontend | Streamlit |
| AI Framework | LangChain |
| Vector DB | ChromaDB (local) |
| LLM | OpenAI GPT-3.5-Turbo |
| Embeddings | OpenAI text-embedding-ada-002 |

---

## Project Structure

```
project/
├── backend/
│   ├── main.py          # FastAPI app + all API endpoints
│   ├── rag_pipeline.py  # Document ingestion, RAG chain, quiz generation
│   ├── db.py            # ChromaDB vector store management
│   ├── models.py        # Pydantic request/response models
│   ├── utils.py         # Helper utilities
│   └── .env             # Environment variables (API keys, config)
│
├── frontend/
│   └── app.py           # Streamlit chat UI
│
├── requirements.txt
└── README.md
```

---

## Setup & Installation

### 1. Clone / navigate to the project directory

```bash
cd project
```

### 2. Create and activate a virtual environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure your OpenAI API key

Edit `backend/.env`:

```env
OPENAI_API_KEY=sk-your-actual-openai-api-key-here
CHROMA_DB_PATH=./chroma_db
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
TOP_K_RESULTS=4
```

> ⚠️ Never commit your `.env` file to version control.

---

## Running the Application

You need **two terminals** — one for the backend, one for the frontend.

### Terminal 1 — Start the FastAPI backend

```bash
cd project/backend
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at: http://localhost:8000  
Interactive docs: http://localhost:8000/docs

### Terminal 2 — Start the Streamlit frontend

```bash
cd project/frontend
streamlit run app.py
```

The UI will open at: http://localhost:8501

---

## How to Use

1. **Upload a PDF** — Click the file uploader in the sidebar and select your syllabus PDF.
2. **Ask questions** — Type any question in the chat box. The AI answers only from your document.
3. **Generate a quiz** — Enter a topic in the sidebar and click "Generate Quiz" to get 5 MCQs.
4. **View sources** — Toggle "Show source chunks" in settings to see which parts of the syllabus were used.
5. **Clear chat** — Use the "Clear Chat" button to start a fresh conversation.

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| POST | `/upload` | Upload and process a PDF |
| POST | `/ask` | Ask a question (RAG) |
| POST | `/quiz` | Generate MCQ quiz |
| DELETE | `/session/{id}` | Clear conversation memory |

### Example: Ask a question

```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What is supervised learning?", "session_id": "student1"}'
```

### Example: Generate a quiz

```bash
curl -X POST http://localhost:8000/quiz \
  -H "Content-Type: application/json" \
  -d '{"topic": "Neural Networks", "num_questions": 5}'
```

---

## Key Design Decisions

### Anti-Hallucination
The LLM prompt explicitly instructs the model to answer **only from provided context**. If the answer isn't in the syllabus, it responds with `"Not in syllabus"`.

### Conversational Memory
Each session maintains a `ConversationBufferMemory` so students can ask follow-up questions naturally.

### Modular Architecture
- `db.py` — all vector store logic isolated here
- `rag_pipeline.py` — all AI/LLM logic isolated here
- `main.py` — only routing and HTTP concerns

### Local Vector Store
ChromaDB runs entirely locally with no external API calls or costs beyond OpenAI.

---

## Configuration Options (`.env`)

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENAI_API_KEY` | — | Your OpenAI API key (required) |
| `CHROMA_DB_PATH` | `./chroma_db` | Where ChromaDB stores its data |
| `CHUNK_SIZE` | `1000` | Characters per text chunk |
| `CHUNK_OVERLAP` | `200` | Overlap between chunks |
| `TOP_K_RESULTS` | `4` | Number of chunks retrieved per query |

---

## Troubleshooting

**"Backend offline" in Streamlit**  
→ Make sure the FastAPI server is running on port 8000.

**"No syllabus documents uploaded"**  
→ Upload a PDF before asking questions.

**OpenAI API errors**  
→ Check your `OPENAI_API_KEY` in `backend/.env`.

**ChromaDB errors on restart**  
→ The `chroma_db/` folder persists data between runs. Delete it to start fresh.
