
import json
from urllib import response

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

def search_chunks(query, document_id, top_k=3):

    query_embedding = embedding_model.encode(query)

    results = collection.query(
        query_embeddings=[query_embedding.tolist()],
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

        chat_key = f"{session_id}_{document_id}"
        if chat_key not in chat_history:
            chat_history[chat_key] = []

        results = search_chunks(
            question,
            document_id
        )

        documents = results.get("documents", [])

        if not documents or len(documents[0]) == 0:
            return {
                "answer": "No relevant answer found.",
                "source": None
            }

        context = "\n".join(documents[0])

        chat_history[chat_key].append(
            {
                "role": "user",
                "content": question
            }
        )

        conversation = ""

        for message in chat_history[chat_key]:

            conversation += (
                f"{message['role']}: "
                f"{message['content']}\n"
            )

        print("\n===== CHAT HISTORY =====")

        for msg in chat_history[chat_key]:
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

Instructions:
- Answer ONLY using the document context.
- Use conversation history only to understand references such as "it", "that", or "the above topic".
- Do NOT use previous answers as factual knowledge.
- If the answer is not found in the document context, reply exactly:

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

        chat_history[chat_key].append(
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
    results = search_chunks(
        topic,
        document_id
    )

    documents = results.get("documents", [])

    if not documents or len(documents[0]) == 0:
        return []

    context = "\n".join(documents[0])

    prompt = f"""
You are an AI Tutor.

Generate exactly {num_questions} multiple-choice questions.

Topic:
{topic}

Document Context:
{context}

Rules:
- Questions must be from the topic only.
- Each question must have 4 options.
- Mention the correct answer.
- Format neatly.
- Do not generate questions from other topics.
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

    return [quiz_text]
def get_db_stats():

    total_chunks = collection.count()

    return {
        "total_chunks": total_chunks
    }

def summarize_document(document_id):

    results = collection.get(
        where={
            "document_id": document_id
        }
    )

    documents = results.get("documents", [])

    if not documents:
        return "Document not found."

    context = "\n".join(documents[:20])

    prompt = f"""
You are an AI Tutor.

Create a concise summary of the following document.

Document:
{context}

Requirements:
- Explain the main topics.
- Keep the summary under 300 words.
- Use simple language.
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
def generate_flashcards(
    document_id,
    num_cards=10
):
    results = search_chunks(
        "important concepts",
        document_id,
        top_k=10
    )

    documents = results.get(
        "documents",
        []
    )

    if not documents or len(documents[0]) == 0:
        return []

    context = "\n".join(documents[0])

    prompt = f"""
Create {num_cards} flashcards from the document.

Format exactly like this:

Question: What is REST?
Answer: Representational State Transfer

Question: What is GET?
Answer: Retrieve data

Only return flashcards.
"""

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {
                "role": "user",
                "content": prompt + "\n\n" + context
            }
        ]
    )

    flashcard_text = response.choices[0].message.content

    flashcards = []

    lines = flashcard_text.split("\n")

    current_question = None

    for line in lines:

        line = line.strip()

        if line.startswith("Question:"):
            current_question = (
                line.replace(
                    "Question:",
                    ""
                ).strip()
            )

        elif (
            line.startswith("Answer:")
            and current_question
        ):
            answer = (
                line.replace(
                    "Answer:",
                    ""
                ).strip()
            )

            flashcards.append(
                {
                    "question": current_question,
                    "answer": answer
                }
            )

            current_question = None

    return flashcards
def generate_study_notes(document_id):

    results = collection.get(
        where={
            "document_id": document_id
        }
    )

    documents = results.get("documents", [])

    if not documents:
        return "Document not found."

    context = "\n".join(documents[:20])

    prompt = f"""
You are an AI Tutor.

Create detailed study notes from the document.

Requirements:
- Use headings
- Use bullet points
- Explain important concepts
- Keep notes easy for revision
- Use only the provided context

Context:
{context}
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
def extract_topics(document_id):

    results = collection.get(
        where={
            "document_id": document_id
        }
    )

    documents = results.get("documents", [])

    if not documents:
        return []

    context = "\n".join(documents[:20])

    prompt = f"""
You are an AI Tutor.

Extract the important topics from the document.

Rules:
- Return only topic names.
- One topic per line.
- No numbering.
- No explanations.

Context:
{context}
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

    topics_text = response.choices[0].message.content

    topics = [
        topic.strip()
        for topic in topics_text.split("\n")
        if topic.strip()
    ]

    return topics


def generate_learning_path(document_id):

    results = search_chunks(
        "main topics",
        document_id,
        top_k=10
    )

    documents = results.get("documents", [])

    if not documents or not documents[0]:
        return []

    context = "\n".join(documents[0])

    prompt = f"""
You are an AI Tutor.

Analyze the document and create a structured learning path.

Rules:
- Extract major topics.
- Arrange from beginner to advanced.
- Each item must have:
  - topic
  - difficulty (Beginner / Intermediate / Advanced)

Return ONLY valid JSON (no markdown, no explanation).

Format:
[
  {{
    "topic": "string",
    "difficulty": "Beginner"
  }}
]

Document:
{context}
"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    raw_output = response.choices[0].message.content

    try:
        # clean + parse JSON safely
        learning_path = json.loads(raw_output)
        return learning_path

    except json.JSONDecodeError:
        # fallback: prevent API crash
        return {
            "error": "Model returned invalid JSON",
            "raw_output": raw_output
        }