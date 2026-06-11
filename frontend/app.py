import streamlit as st
import requests

# -----------------------------
# PAGE CONFIG
# -----------------------------
st.set_page_config(
    page_title="AI Tutor",
    page_icon="📚",
    layout="wide"
)

# -----------------------------
# SESSION STATE
# -----------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

# -----------------------------
# TITLE
# -----------------------------
st.title("📚 AI Tutor")
menu = st.sidebar.radio(
    "Navigation",
    [
        "Ask Questions",
        "Quiz",
        "Summary",
        "Flashcards",
        "Study Notes",
        "Topics",
        "Learning Path",
        "Progress"
    ]
)
# -----------------------------
# HEALTH CHECK
# -----------------------------
try:
    response = requests.get(
        "http://127.0.0.1:8000/health"
    )

    if response.status_code == 200:
        st.success(
            response.json()["status"]
        )

except Exception:
    st.error(
        "Backend not running"
    )

# -----------------------------
# PDF UPLOAD
# -----------------------------
st.header("📤 Upload PDF")

uploaded_file = st.file_uploader(
    "Choose a PDF",
    type=["pdf"]
)

if uploaded_file:

    if st.button("Upload PDF"):

        files = {
            "file": (
                uploaded_file.name,
                uploaded_file,
                "application/pdf"
            )
        }

        response = requests.post(
            "http://127.0.0.1:8000/upload",
            files=files
        )

        st.json(
            response.json()
        )

# -----------------------------
# DOCUMENT LIST
# -----------------------------
st.header("📄 Available Documents")

selected_document = None

try:

    response = requests.get(
        "http://127.0.0.1:8000/documents/list"
    )

    documents = response.json().get(
        "documents",
        []
    )

    if documents:

        selected_document = st.selectbox(
            "Select Document",
            documents
        )

    else:
        st.warning(
            "No documents uploaded yet"
        )

except Exception:

    st.error(
        "Unable to load documents"
    )

if menu == "Summary":

    st.header("📄 Document Summary")

    if st.button("Generate Summary"):

        payload = {
            "document_id": selected_document
        }

        response = requests.post(
            "http://127.0.0.1:8000/summary",
            json=payload
        )

        data = response.json()

        st.markdown(data["summary"])

# -----------------------------
# ASK QUESTION
# -----------------------------
st.header("💬 Ask Questions")

session_id = st.text_input(
    "Session ID",
    value="user1"
)

question = st.text_area(
    "Ask a Question"
)

if st.button("Ask AI Tutor"):

    if not selected_document:

        st.error(
            "Please select a document"
        )

    elif not question.strip():

        st.error(
            "Please enter a question"
        )

    else:

        payload = {
            "question": question,
            "session_id": session_id,
            "document_id": selected_document
        }

        response = requests.post(
            "http://127.0.0.1:8000/ask",
            json=payload
        )

        data = response.json()

        st.session_state.messages.append(
            {
                "role": "user",
                "content": question
            }
        )

        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": data["answer"]
            }
        )

# -----------------------------
# CLEAR CHAT
# -----------------------------
if st.button("Clear Chat"):

    st.session_state.messages = []

    st.rerun()

# -----------------------------
# CHAT HISTORY
# -----------------------------
st.header("🧠 Conversation")

for message in st.session_state.messages:

    with st.chat_message(
        message["role"]
    ):

        st.write(
            message["content"]
        )

# -----------------------------
# QUIZ GENERATOR
# -----------------------------
st.header("📝 Quiz Generator")

quiz_topic = st.text_input(
    "Quiz Topic",
    placeholder="Example: Cypress"
)

num_questions = st.number_input(
    "Number of Questions",
    min_value=1,
    max_value=10,
    value=5
)

if st.button("Generate Quiz"):

    if not selected_document:

        st.error(
            "Please select a document"
        )

    else:

        payload = {
            "topic": quiz_topic,
            "document_id": selected_document,
            "num_questions": num_questions
        }

        response = requests.post(
            "http://127.0.0.1:8000/quiz",
            json=payload
        )

        data = response.json()

        st.subheader("Generated Quiz")

        st.markdown(
            data["questions"][0]
        ) 
if menu == "Flashcards":

    st.header("🃏 Flashcards")

    num_cards = st.number_input(
        "Number of Flashcards",
        min_value=1,
        max_value=20,
        value=5
    )

    if st.button("Generate Flashcards"):

        payload = {
            "document_id": selected_document,
            "num_cards": num_cards
        }

        response = requests.post(
            "http://127.0.0.1:8000/flashcards",
            json=payload
        )

        data = response.json()

        for card in data["flashcards"]:

            with st.expander(card["question"]):

                st.write(card["answer"])
if menu == "Study Notes":

    st.header("📝 Study Notes")

    if st.button("Generate Notes"):

        payload = {
            "document_id": selected_document
        }

        response = requests.post(
            "http://127.0.0.1:8000/notes",
            json=payload
        )

        data = response.json()

        st.markdown(data["notes"])
if menu == "Topics":

    st.header("📚 Extract Topics")

    if st.button("Extract Topics"):

        payload = {
            "document_id": selected_document
        }

        response = requests.post(
            "http://127.0.0.1:8000/topics",
            json=payload
        )

        data = response.json()

        for topic in data["topics"]:

            st.write("•", topic)
if menu == "Learning Path":

    st.header("🎯 Learning Path")

    if st.button(
        "Generate Learning Path",
        key="learning_path_btn"
    ):

        payload = {
            "document_id": selected_document
        }

        response = requests.post(
            "http://127.0.0.1:8000/learning-path",
            json=payload
        )

        st.write(
            "Status Code:",
            response.status_code
        )

        st.write(
            "Response Text:",
            response.text
        )

        if response.status_code == 200:

            data = response.json()

            for step in data["topics"]:

                st.write(
                    "➡️",
                    step
                )

        else:

            st.error(
                "Learning Path API failed"
            )
