"""
ChromaDB singleton using google-genai SDK for embeddings.
Supports both AIzaSy and AQ. API key formats.
"""

import os
import sys
import logging
from pathlib import Path
from typing import List, Optional

sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv(dotenv_path=Path(__file__).parent / ".env")

from google import genai as google_genai          # google-genai SDK
from chromadb import PersistentClient
from chromadb.utils.embedding_functions import EmbeddingFunction
from langchain_core.documents import Document as LCDoc

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Gemini embedding function (ChromaDB-compatible)
# ---------------------------------------------------------------------------

class GeminiEmbeddingFunction(EmbeddingFunction):
    """
    Calls Gemini text-embedding-004 via google-genai SDK.
    Works with both AIzaSy and AQ. key formats.
    """

    def __init__(self):
        key = os.getenv("GOOGLE_API_KEY", "").strip()
        if not key:
            raise ValueError(
                "GOOGLE_API_KEY missing. "
                "Set it in backend/.env — https://aistudio.google.com/apikey"
            )
        self._client = google_genai.Client(api_key=key)
        self._model  = "text-embedding-004"
        logger.info(f"[EMBED] Initialized with model: {self._model}")

    def __call__(self, input: List[str]) -> List[List[float]]:
        embeddings = []
        for text in input:
            try:
                result = self._client.models.embed_content(
                    model=self._model,
                    contents=text,
                )
                embeddings.append(result.embeddings[0].values)
            except Exception as e:
                logger.error(f"[EMBED] Failed: {e}")
                raise
        return embeddings


# ---------------------------------------------------------------------------
# ChromaDB singleton
# ---------------------------------------------------------------------------

_chroma_client = None
_collection    = None


def _get_collection():
    global _chroma_client, _collection

    if _collection is not None:
        return _collection

    chroma_path = os.getenv("CHROMA_DB_PATH", "./chroma_db")
    if not Path(chroma_path).is_absolute():
        chroma_path = str(Path(__file__).parent / chroma_path)

    os.makedirs(chroma_path, exist_ok=True)
    logger.info(f"[CHROMA] Connecting at: {chroma_path}")

    _chroma_client = PersistentClient(path=chroma_path)
    _collection = _chroma_client.get_or_create_collection(
        name="ai_tutor_docs",
        embedding_function=GeminiEmbeddingFunction(),
    )
    logger.info(f"[CHROMA] Collection count: {_collection.count()}")
    return _collection


def reset_vector_store() -> None:
    global _chroma_client, _collection
    _chroma_client = None
    _collection    = None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def add_documents(documents) -> int:
    if not documents:
        return 0

    col = _get_collection()
    existing = col.count()

    ids       = [f"chunk_{existing + i}" for i in range(len(documents))]
    texts     = [doc.page_content for doc in documents]
    metadatas = [doc.metadata or {} for doc in documents]

    col.add(ids=ids, documents=texts, metadatas=metadatas)
    reset_vector_store()
    logger.info(f"[CHROMA] Added {len(texts)} chunks (total now ~{existing + len(texts)})")
    return len(texts)


def get_vector_store():
    return _VectorStoreAdapter()


class _VectorStoreAdapter:
    def as_retriever(self, search_kwargs=None):
        return _RetrieverAdapter((search_kwargs or {}).get("k", 4))


class _RetrieverAdapter:
    def __init__(self, k: int):
        self.k = k

    def invoke(self, query: str) -> List[LCDoc]:
        return similarity_search(query, k=self.k)


def similarity_search(query: str, k: int = 4) -> List[LCDoc]:
    col = _get_collection()
    if col.count() == 0:
        return []

    results = col.query(
        query_texts=[query],
        n_results=min(k, col.count()),
        include=["documents", "metadatas"],
    )

    return [
        LCDoc(page_content=text, metadata=meta or {})
        for text, meta in zip(
            results["documents"][0],
            results["metadatas"][0],
        )
    ]


def collection_is_empty() -> bool:
    try:
        return _get_collection().count() == 0
    except Exception:
        return True
