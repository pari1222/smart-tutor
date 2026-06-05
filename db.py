"""
ChromaDB singleton using Google Gemini embeddings.
"""

import os
import sys
import logging
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv(dotenv_path=Path(__file__).parent / ".env")

from langchain_chroma import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings

logger = logging.getLogger(__name__)

_vector_store: Optional[Chroma] = None


def get_embeddings() -> GoogleGenerativeAIEmbeddings:
    return GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-001",
        google_api_key=os.getenv("GOOGLE_API_KEY"),
    )


def get_vector_store() -> Chroma:
    global _vector_store

    if _vector_store is None:
        chroma_path = os.getenv("CHROMA_DB_PATH", "./chroma_db")

        if not Path(chroma_path).is_absolute():
            chroma_path = str(Path(__file__).parent / chroma_path)

        os.makedirs(chroma_path, exist_ok=True)
        logger.info(f"Initializing ChromaDB at: {chroma_path}")

        _vector_store = Chroma(
            collection_name="ai_tutor_docs",
            embedding_function=get_embeddings(),
            persist_directory=chroma_path,
        )

    return _vector_store


def reset_vector_store() -> None:
    global _vector_store
    _vector_store = None


def add_documents(documents) -> int:
    if not documents:
        return 0
    store = get_vector_store()
    store.add_documents(documents)
    reset_vector_store()
    logger.info(f"Stored {len(documents)} chunks")
    return len(documents)


def similarity_search(query: str, k: int = 4):
    store = get_vector_store()
    return store.similarity_search(query, k=k)


def collection_is_empty() -> bool:
    try:
        store = get_vector_store()
        return store._collection.count() == 0
    except Exception:
        return True
