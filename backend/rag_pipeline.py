
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

chat_history = {}

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

def store_chunks(chunks, document_id):

    for chunk in chunks:

        embedding = embedding_model.encode(chunk)

        collection.add(
            documents=[chunk],
            embeddings=[embedding.tolist()],
            ids=[str(uuid.uuid4())],
            metadatas=[
                {
                    "document_id": document_id
                }
            ]
        )

def search_chunks(
    query,
    document_id,
    top_k=3
):
    query_embedding = embedding_model.encode(query)

    results = collection.query(
        query_embeddings=[
            query_embedding.tolist()
        ],
        n_results=top_k,
        where={
            "document_id": document_id
        }
    )

    return results
def ask_pdf(
    question,
    session_id,
    document_id
):

    try:
        if session_id not in chat_history:
            chat_history[session_id] = []

        results = search_chunks(question, document_id)

        documents = results.get("documents", [])

        if not documents or len(documents[0]) == 0:
            return {
                "answer": "No relevant answer found.",
                "source": None
            }

        context = "\n".join(documents[0])
        chat_history[session_id].append(
            {
                "role": "user",
                "content": question
            }
        )
        conversation = ""

        for message in chat_history[session_id]:

            conversation += (
                f"{message['role']}: "
                f"{message['content']}\n"
            )
        print("\n===== CHAT HISTORY =====")

        for msg in chat_history[session_id]:
            print(msg)

        print("========================\n")
        prompt = f"""
You are an AI Tutor.

Previous Conversation:
{conversation}

Document Context:
{context}

Current Question:
{question}

Answer using the document context and conversation history.

If the answer is not available in the document context, reply:
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

        answer = response.choices[0].message.content
        chat_history[session_id].append(
            {
                "role": "assistant",
                "content": answer
            }
)

        return {
            "answer": answer,
            "source": documents[0][0][:300]
        }
    except Exception as e:

        print("GROQ ERROR:", str(e))

        return {
            "answer": f"Error: {str(e)}",
            "source": None
        }

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

    store_chunks(
            chunks,
            os.path.basename(file_path)
    )

    print("\n===== CHUNK PREVIEW =====\n")

    for index, chunk in enumerate(chunks[:3]):

        print(f"\nChunk {index + 1}:\n")

        print(chunk[:300])

    print("\n=========================\n")
    page_count = len(reader.pages)
    return {
        "status": "PDF processed successfully",
        "characters": len(full_text),
        "pages":page_count,
        "chunks": len(chunks),
        "stored_in_vector_db": True
    }

def generate_quiz_from_pdf(
    topic,
    document_id,
    num_questions=5
):
    results = search_chunks(topic, document_id)

    documents = results.get("documents", [])

    if not documents or len(documents[0]) == 0:
        return ["No content found for quiz generation"]

    context = "\n".join(documents[0])

    prompt = f"""
You are an AI Tutor.

Using ONLY the provided context, generate exactly {num_questions}
multiple-choice quiz questions.

Rules:
- Return only the quiz questions.
- Each question must have 4 options.
- Do not include introductions.
- Do not include explanations.
- Do not include any text before Question 1.

Context:
{context}
"""

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    quiz_text = response.choices[0].message.content

    questions = [
        line.strip()
        for line in quiz_text.split("\n")
        if line.strip()
    ]

    return questions
def get_db_stats():

    total_chunks = collection.count()

    return {
        "total_chunks": total_chunks
    }

