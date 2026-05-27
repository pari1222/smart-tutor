from pypdf import PdfReader

import chromadb

from sentence_transformers import SentenceTransformer
from transformers import pipeline
from typer import prompt


embedding_model = SentenceTransformer(
    "all-MiniLM-L6-v2"
)
generator = pipeline(
    "text-generation",
    model="distilgpt2"
)

chroma_client = chromadb.Client()

collection = chroma_client.get_or_create_collection(
    name="pdf_documents"
)


def chunk_text(text, chunk_size=500):

    chunks = []

    for i in range(0, len(text), chunk_size):

        chunk = text[i:i + chunk_size]

        chunks.append(chunk)

    return chunks


def store_chunks(chunks):

    for index, chunk in enumerate(chunks):

        embedding = embedding_model.encode(chunk)

        collection.add(
            documents=[chunk],

            embeddings=[embedding.tolist()],

            ids=[f"chunk_{index}"]
        )
def search_chunks(query, top_k=3):

    query_embedding = embedding_model.encode(query)

    results = collection.query(
        query_embeddings=[query_embedding.tolist()],
        n_results=top_k
    )

    return results
def ask_pdf(question):

    results = search_chunks(question)

    documents = results.get("documents", [])

    if not documents:
        return "No relevant answer found."

    matched_chunks = documents[0]

    context = "\n".join(matched_chunks)

    prompt = f"""
    Context:
    {context}

    Question:
    {question}

Answer briefly and clearly.
"""

    response = generator(
        prompt,
        max_new_tokens=100
    )

    generated_text = response[0]["generated_text"]

    answer = generated_text.replace(prompt, "").strip()

    return answer

def process_pdf(file_path):

    reader = PdfReader(file_path)

    full_text = ""

    for page in reader.pages:

        text = page.extract_text()

        if text:
            full_text += text

    chunks = chunk_text(full_text)

    store_chunks(chunks)

    print("\n===== CHUNK PREVIEW =====\n")

    for index, chunk in enumerate(chunks[:3]):

        print(f"\nChunk {index + 1}:\n")

        print(chunk[:300])

    print("\n=========================\n")

    return {
        "status": "PDF processed successfully",
        "characters": len(full_text),
        "chunks": len(chunks),
        "stored_in_vector_db": True
    }
