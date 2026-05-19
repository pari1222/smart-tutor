"""
RAG Pipeline: PDF ingestion, question answering, and quiz generation.
Uses Google Gemini for both LLM and embeddings.
"""

import os
import sys
import json
import re
import logging
from pathlib import Path
from typing import List, Dict, Any

sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv(dotenv_path=Path(__file__).parent / ".env")

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser

from db import add_documents, get_vector_store, similarity_search, collection_is_empty

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# LLM
# ---------------------------------------------------------------------------

def get_llm() -> ChatGoogleGenerativeAI:
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY not set in .env")
    return ChatGoogleGenerativeAI(
        model="gemini-2.0-flash",
        temperature=0.2,
        google_api_key=api_key,
    )

# ---------------------------------------------------------------------------
# Session memory
# ---------------------------------------------------------------------------

_session_histories: Dict[str, List] = {}

def get_history(session_id: str) -> List:
    if session_id not in _session_histories:
        _session_histories[session_id] = []
    return _session_histories[session_id]

def clear_memory(session_id: str) -> None:
    _session_histories[session_id] = []

# ---------------------------------------------------------------------------
# Prompts
# ---------------------------------------------------------------------------

RAG_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are a helpful AI tutor.
Answer ONLY using the provided context below.
If the answer is not in the context, say exactly: "Not in syllabus"

Context:
{context}"""),
    MessagesPlaceholder(variable_name="chat_history"),
    ("human", "{question}"),
])

QUIZ_SYSTEM_PROMPT = """You are an expert quiz creator.
Generate {num_questions} MCQs strictly from the context below.

Rules:
- Each question has exactly 4 options labelled A., B., C., D.
- The answer field must be the full text of the correct option.
- Return ONLY a valid JSON array, no markdown fences, no extra text.

Format:
[
  {{
    "question": "...",
    "options": ["A. ...", "B. ...", "C. ...", "D. ..."],
    "answer": "A. ..."
  }}
]

Context:
{context}"""

# ---------------------------------------------------------------------------
# PDF Ingestion
# ---------------------------------------------------------------------------

def ingest_pdf(filepath: str, filename: str = "") -> int:
    logger.info(f"Loading PDF: {filename or filepath}")

    loader = PyPDFLoader(filepath)
    pages: List[Document] = loader.load()

    chunk_size = int(os.getenv("CHUNK_SIZE", 1000))
    chunk_overlap = int(os.getenv("CHUNK_OVERLAP", 200))

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )
    chunks = splitter.split_documents(pages)

    if not chunks:
        raise ValueError("No text could be extracted from the PDF.")

    for chunk in chunks:
        if filename:
            chunk.metadata["source"] = filename

    stored = add_documents(chunks)
    logger.info(f"Stored {stored} chunks")
    return stored

# ---------------------------------------------------------------------------
# Question Answering
# ---------------------------------------------------------------------------

def answer_question(question: str, session_id: str = "default") -> Dict[str, Any]:
    if collection_is_empty():
        return {"answer": "No documents uploaded yet. Please upload a PDF first.", "sources": []}

    retriever = get_vector_store().as_retriever(search_kwargs={"k": int(os.getenv("TOP_K_RESULTS", 4))})
    docs = retriever.invoke(question)

    context = "\n\n---\n\n".join(doc.page_content for doc in docs)
    history = get_history(session_id)

    chain = RAG_PROMPT | get_llm() | StrOutputParser()
    answer = chain.invoke({
        "context": context,
        "chat_history": history,
        "question": question,
    })

    history.append(HumanMessage(content=question))
    history.append(AIMessage(content=answer))

    sources = []
    for doc in docs:
        snippet = doc.page_content[:200].replace("\n", " ")
        src = doc.metadata.get("source", "unknown")
        sources.append(f"{src}: {snippet}...")

    return {"answer": answer, "sources": sources}

# ---------------------------------------------------------------------------
# Quiz Generation
# ---------------------------------------------------------------------------

def generate_quiz(topic: str, num_questions: int = 5) -> list:
    if collection_is_empty():
        raise ValueError("Upload a PDF first before generating a quiz.")

    docs = similarity_search(topic, k=8)
    if not docs:
        raise ValueError("No relevant content found for this topic.")

    context = "\n\n---\n\n".join(doc.page_content for doc in docs)

    prompt = ChatPromptTemplate.from_messages([
        ("system", QUIZ_SYSTEM_PROMPT),
        ("human", "Generate {num_questions} MCQ questions about: {topic}"),
    ])

    chain = prompt | get_llm() | StrOutputParser()
    raw = chain.invoke({"context": context, "topic": topic, "num_questions": num_questions})

    # Strip markdown fences if present
    clean = raw.strip()
    clean = re.sub(r"^```(?:json)?\s*", "", clean)
    clean = re.sub(r"\s*```$", "", clean)

    questions = json.loads(clean.strip())

    if not isinstance(questions, list):
        raise ValueError("LLM did not return a JSON array.")

    return questions
