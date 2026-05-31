
from pypdf import PdfReader
from groq import Groq
import os
import chromadb
import uuid
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

load_dotenv()

embedding_model = SentenceTransformer(
    "all-MiniLM-L6-v2"
)
groq_key = os.getenv("GROQ_KEY")

if not groq_key:
    raise ValueError(
        "GROQ_KEY not found in .env file"
    )

client = Groq(api_key=groq_key)


chroma_client = chromadb.PersistentClient(
    path="chroma_db"
)
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

    for chunk in chunks:
        embedding = embedding_model.encode(chunk)

        collection.add(
            documents=[chunk],

            embeddings=[embedding.tolist()],

            ids=[str(uuid.uuid4())]
        )

def search_chunks(query, top_k=3):

    query_embedding = embedding_model.encode(query)

    results = collection.query(
        query_embeddings=[query_embedding.tolist()],
        n_results=top_k
    )

    return results

def ask_pdf(question):

    try:

        results = search_chunks(question)

        documents = results.get("documents", [])

        if not documents or len(documents[0]) == 0:
            return "No relevant answer found."

        context = "\n".join(documents[0])

        prompt = f"""
You are an AI Tutor.

Answer the question using ONLY the provided context.

Context:
{context}

Question:
{question}

If the answer is not available in the context, reply:
I could not find the answer in the uploaded document.
"""

        response = client.chat.completions.create(
           model="llama-3.3-70b-versatile",
           messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        return response.choices[0].message.content

    except Exception as e:

        print("GROQ ERROR:", str(e))

        return f"Error: {str(e)}"

def process_pdf(file_path):

    reader = PdfReader(file_path)

    full_text = ""

    for page in reader.pages:

        text = page.extract_text()

        if text:
            full_text += text

    if not full_text.strip():
        raise ValueError(
        "No text could be extracted from PDF"
    )

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
