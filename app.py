"""
Module 4 — Frontend Student Panel
Owner: Team Member 4
Files owned: frontend/app.py → show_student() function and all API helper functions

Responsibilities:
- Student chat interface (chat bubbles, message history)
- Source chunks display toggle
- PDF viewer tab (dropdown + iframe)
- Quiz tab (radio buttons, reveal answer)
- All api_* helper functions (api_ask, api_quiz, api_list_pdfs, etc.)
- Session management (clear chat, new session ID)
"""

import streamlit as st
import requests
import uuid
import json
from typing import Optional

# ──────────────────────────────────────────────
# Configuration
# ──────────────────────────────────────────────

BASE_URL = "http://localhost:8000"   # Change to your backend URL

# ──────────────────────────────────────────────
# Custom CSS — Soft Academic / Clean UI Theme
# ──────────────────────────────────────────────

CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Lora:ital,wght@0,400;0,600;1,400&family=DM+Sans:wght@300;400;500;600&family=JetBrains+Mono:wght@400;500&display=swap');

/* ── Root palette ── */
:root {
    --bg:           #F7F5F0;
    --surface:      #FFFFFF;
    --surface-alt:  #F0EDE6;
    --border:       #E2DDD6;
    --accent:       #2C6E49;
    --accent-soft:  #D4EDDA;
    --accent-mid:   #52A875;
    --user-bubble:  #2C6E49;
    --user-text:    #FFFFFF;
    --bot-bubble:   #FFFFFF;
    --bot-text:     #1A1A1A;
    --muted:        #7A7570;
    --danger:       #C0392B;
    --warning:      #E67E22;
    --shadow:       0 2px 12px rgba(0,0,0,0.07);
    --radius:       12px;
    --radius-bubble:18px;
}

/* ── Global ── */
html, body, [data-testid="stAppViewContainer"] {
    background-color: var(--bg) !important;
    font-family: 'DM Sans', sans-serif;
    color: var(--bot-text);
}

[data-testid="stSidebar"] {
    background-color: #1E2D24 !important;
    border-right: 1px solid #2C4A36;
}

[data-testid="stSidebar"] * {
    color: #E8F5EC !important;
}

[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 {
    font-family: 'Lora', serif !important;
    color: #A8D5B5 !important;
}

/* ── Main header ── */
.student-header {
    background: linear-gradient(135deg, #2C6E49 0%, #1A4530 100%);
    color: white;
    padding: 1.5rem 2rem;
    border-radius: var(--radius);
    margin-bottom: 1.5rem;
    display: flex;
    align-items: center;
    gap: 1rem;
    box-shadow: 0 4px 20px rgba(44,110,73,0.25);
}

.student-header h1 {
    font-family: 'Lora', serif;
    font-size: 1.6rem;
    font-weight: 600;
    margin: 0;
    color: white !important;
}

.student-header p {
    margin: 0.25rem 0 0;
    font-size: 0.85rem;
    opacity: 0.8;
    color: #C8E6D0;
}

/* ── Tab bar ── */
[data-testid="stTabs"] [data-baseweb="tab-list"] {
    background: var(--surface-alt);
    border-radius: var(--radius);
    padding: 4px;
    gap: 4px;
    border: 1px solid var(--border);
}

[data-testid="stTabs"] [data-baseweb="tab"] {
    border-radius: 8px;
    font-family: 'DM Sans', sans-serif;
    font-weight: 500;
    font-size: 0.9rem;
    padding: 0.5rem 1.2rem;
    color: var(--muted);
    transition: all 0.2s;
}

[data-testid="stTabs"] [aria-selected="true"] {
    background: var(--accent) !important;
    color: white !important;
}

/* ── Chat container ── */
.chat-container {
    display: flex;
    flex-direction: column;
    gap: 1rem;
    padding: 1rem 0;
    max-height: 520px;
    overflow-y: auto;
    scrollbar-width: thin;
    scrollbar-color: var(--accent-soft) transparent;
}

.chat-container::-webkit-scrollbar { width: 5px; }
.chat-container::-webkit-scrollbar-thumb {
    background: var(--accent-soft);
    border-radius: 10px;
}

/* ── Bubble base ── */
.bubble-row {
    display: flex;
    align-items: flex-end;
    gap: 0.6rem;
    animation: fadeUp 0.3s ease both;
}

@keyframes fadeUp {
    from { opacity: 0; transform: translateY(8px); }
    to   { opacity: 1; transform: translateY(0); }
}

.bubble-row.user  { flex-direction: row-reverse; }

.avatar {
    width: 32px;
    height: 32px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.85rem;
    flex-shrink: 0;
    font-weight: 600;
}

.avatar.bot  { background: var(--accent-soft); color: var(--accent); border: 2px solid var(--accent-mid); }
.avatar.user { background: var(--user-bubble); color: white; }

.bubble {
    max-width: 72%;
    padding: 0.75rem 1rem;
    border-radius: var(--radius-bubble);
    font-size: 0.925rem;
    line-height: 1.6;
    box-shadow: var(--shadow);
}

.bubble.user {
    background: var(--user-bubble);
    color: var(--user-text);
    border-bottom-right-radius: 4px;
}

.bubble.bot {
    background: var(--bot-bubble);
    color: var(--bot-text);
    border-bottom-left-radius: 4px;
    border: 1px solid var(--border);
}

.bubble-timestamp {
    font-size: 0.7rem;
    opacity: 0.5;
    margin-top: 4px;
    text-align: right;
}

/* ── Source chunks ── */
.source-chunk {
    background: var(--surface-alt);
    border: 1px solid var(--border);
    border-left: 3px solid var(--accent-mid);
    border-radius: 8px;
    padding: 0.75rem 1rem;
    font-family: 'DM Sans', sans-serif;
    font-size: 0.82rem;
    line-height: 1.55;
    color: #333;
    margin-bottom: 0.5rem;
}

.source-chunk .chunk-header {
    font-size: 0.72rem;
    font-weight: 600;
    color: var(--accent);
    text-transform: uppercase;
    letter-spacing: 0.04em;
    margin-bottom: 0.4rem;
}

.chunk-text {
    color: var(--muted);
    font-style: italic;
}

/* ── Quiz card ── */
.quiz-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 1.5rem;
    box-shadow: var(--shadow);
    margin-bottom: 1rem;
}

.quiz-question {
    font-family: 'Lora', serif;
    font-size: 1.05rem;
    font-weight: 600;
    color: #1A1A1A;
    margin-bottom: 1rem;
    line-height: 1.5;
}

.quiz-correct {
    background: var(--accent-soft);
    border: 1px solid var(--accent-mid);
    border-radius: 8px;
    padding: 0.75rem 1rem;
    color: var(--accent);
    font-weight: 500;
    margin-top: 0.75rem;
}

.quiz-explanation {
    background: #FFF9E6;
    border: 1px solid #F0C040;
    border-radius: 8px;
    padding: 0.75rem 1rem;
    color: #7A5800;
    font-size: 0.88rem;
    margin-top: 0.5rem;
    line-height: 1.5;
}

/* ── Session badge ── */
.session-badge {
    background: rgba(255,255,255,0.08);
    border: 1px solid rgba(255,255,255,0.15);
    border-radius: 20px;
    padding: 0.3rem 0.75rem;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.68rem;
    color: #A8D5B5;
    margin-top: 0.5rem;
    word-break: break-all;
}

/* ── Input area ── */
.stTextInput > div > div > input,
.stTextArea textarea {
    background: var(--surface) !important;
    border: 1.5px solid var(--border) !important;
    border-radius: 10px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.9rem !important;
    transition: border-color 0.2s;
}

.stTextInput > div > div > input:focus,
.stTextArea textarea:focus {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 3px rgba(44,110,73,0.12) !important;
}

/* ── Buttons ── */
.stButton > button {
    background: var(--accent) !important;
    color: white !important;
    border: none !important;
    border-radius: 9px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 500 !important;
    font-size: 0.88rem !important;
    padding: 0.5rem 1.25rem !important;
    transition: all 0.2s !important;
    box-shadow: 0 2px 8px rgba(44,110,73,0.2) !important;
}

.stButton > button:hover {
    background: #1A4530 !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 14px rgba(44,110,73,0.3) !important;
}

/* ── Danger button ── */
.btn-danger > button {
    background: #C0392B !important;
    box-shadow: 0 2px 8px rgba(192,57,43,0.2) !important;
}

.btn-danger > button:hover {
    background: #922B21 !important;
}

/* ── Info / warning boxes ── */
.info-box {
    background: #EAF4FF;
    border: 1px solid #B3D4F5;
    border-radius: 8px;
    padding: 0.75rem 1rem;
    font-size: 0.85rem;
    color: #1A5276;
}

.warn-box {
    background: #FFF3E0;
    border: 1px solid #FFCC80;
    border-radius: 8px;
    padding: 0.75rem 1rem;
    font-size: 0.85rem;
    color: #7D4600;
}

/* ── Selectbox ── */
[data-testid="stSelectbox"] > div {
    border-radius: 9px !important;
    border-color: var(--border) !important;
}

/* ── Divider ── */
hr { border-color: var(--border) !important; }

/* ── PDF iframe ── */
.pdf-frame {
    width: 100%;
    height: 680px;
    border: 1px solid var(--border);
    border-radius: var(--radius);
    box-shadow: var(--shadow);
}

/* ── Expander ── */
[data-testid="stExpander"] {
    border: 1px solid var(--border) !important;
    border-radius: 9px !important;
    background: var(--surface-alt) !important;
}

/* ── Spinner ── */
[data-testid="stSpinner"] { color: var(--accent) !important; }

/* ── Status dots ── */
.status-dot {
    display: inline-block;
    width: 8px;
    height: 8px;
    border-radius: 50%;
    margin-right: 6px;
}
.status-dot.online  { background: #27AE60; }
.status-dot.offline { background: #E74C3C; }
</style>
"""


# ──────────────────────────────────────────────
# API Helper Functions
# ──────────────────────────────────────────────

def api_ask(
    question: str,
    session_id: str,
    pdf_name: Optional[str] = None,
    top_k: int = 5,
) -> dict:
    """
    POST /ask  →  { answer: str, sources: list[dict] }
    Returns a dict with keys 'answer' and 'sources'.
    On error returns {'answer': <error message>, 'sources': []}.
    """
    payload = {
        "question": question,
        "session_id": session_id,
        "top_k": top_k,
    }
    if pdf_name:
        payload["pdf_name"] = pdf_name

    try:
        resp = requests.post(f"{BASE_URL}/ask", json=payload, timeout=60)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.ConnectionError:
        return {
            "answer": "⚠️ Cannot reach the backend server. Is it running?",
            "sources": [],
        }
    except requests.exceptions.Timeout:
        return {
            "answer": "⚠️ The request timed out. The server may be overloaded.",
            "sources": [],
        }
    except requests.exceptions.HTTPError as e:
        return {
            "answer": f"⚠️ Server error {e.response.status_code}: {e.response.text[:200]}",
            "sources": [],
        }
    except Exception as e:
        return {"answer": f"⚠️ Unexpected error: {str(e)}", "sources": []}


def api_quiz(
    pdf_name: str,
    num_questions: int = 5,
    topic: Optional[str] = None,
) -> list[dict]:
    """
    POST /quiz  →  list of { question, choices, answer, explanation }
    Returns [] on error.
    """
    payload = {"pdf_name": pdf_name, "num_questions": num_questions}
    if topic:
        payload["topic"] = topic

    try:
        resp = requests.post(f"{BASE_URL}/quiz", json=payload, timeout=90)
        resp.raise_for_status()
        data = resp.json()
        return data if isinstance(data, list) else data.get("questions", [])
    except requests.exceptions.ConnectionError:
        st.error("⚠️ Cannot reach the backend server.")
        return []
    except requests.exceptions.HTTPError as e:
        st.error(f"⚠️ Server error {e.response.status_code}: {e.response.text[:200]}")
        return []
    except Exception as e:
        st.error(f"⚠️ Quiz generation failed: {str(e)}")
        return []


def api_list_pdfs() -> list[str]:
    """
    GET /pdfs  →  list of PDF filename strings.
    Returns [] on error.
    """
    try:
        resp = requests.get(f"{BASE_URL}/pdfs", timeout=15)
        resp.raise_for_status()
        data = resp.json()
        return data if isinstance(data, list) else data.get("pdfs", [])
    except Exception:
        return []


def api_get_pdf_url(pdf_name: str) -> str:
    """Returns the backend URL for streaming/viewing a PDF in an iframe."""
    return f"{BASE_URL}/pdfs/{pdf_name}"


def api_health() -> bool:
    """GET /health  →  True if backend is alive, False otherwise."""
    try:
        resp = requests.get(f"{BASE_URL}/health", timeout=5)
        return resp.status_code == 200
    except Exception:
        return False


def api_clear_session(session_id: str) -> bool:
    """
    DELETE /session/{session_id}  →  True on success.
    Tells the backend to drop this session's chat history.
    """
    try:
        resp = requests.delete(f"{BASE_URL}/session/{session_id}", timeout=10)
        return resp.status_code in (200, 204)
    except Exception:
        return False


# ──────────────────────────────────────────────
# Session-state Helpers
# ──────────────────────────────────────────────

def _init_session() -> None:
    """Initialise Streamlit session state keys (idempotent)."""
    if "session_id" not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
    if "messages" not in st.session_state:
        st.session_state.messages = []          # list[{role, content, sources}]
    if "show_sources" not in st.session_state:
        st.session_state.show_sources = False
    if "quiz_data" not in st.session_state:
        st.session_state.quiz_data = []         # loaded quiz questions
    if "quiz_revealed" not in st.session_state:
        st.session_state.quiz_revealed = {}     # {idx: True/False}
    if "quiz_selected" not in st.session_state:
        st.session_state.quiz_selected = {}     # {idx: chosen_option}
    if "selected_pdf" not in st.session_state:
        st.session_state.selected_pdf = None


def _new_session() -> None:
    """Generate a brand-new session ID and wipe chat history."""
    api_clear_session(st.session_state.session_id)   # best-effort backend clear
    st.session_state.session_id = str(uuid.uuid4())
    st.session_state.messages = []
    st.session_state.quiz_data = []
    st.session_state.quiz_revealed = {}
    st.session_state.quiz_selected = {}


def _clear_chat() -> None:
    """Clear only the chat messages; keep the session ID."""
    api_clear_session(st.session_state.session_id)
    st.session_state.messages = []


# ──────────────────────────────────────────────
# Rendering Helpers
# ──────────────────────────────────────────────

def _render_bubble(role: str, content: str, sources: list[dict] | None = None) -> None:
    """Render a single chat bubble (HTML via st.markdown)."""
    is_user = role == "user"
    bubble_cls = "user" if is_user else "bot"
    avatar_cls  = "user" if is_user else "bot"
    avatar_icon = "🎓" if is_user else "🤖"
    row_cls     = "user" if is_user else "bot"

    # Escape any stray HTML in the content
    safe_content = content.replace("<", "&lt;").replace(">", "&gt;")

    html = f"""
    <div class="bubble-row {row_cls}">
        <div class="avatar {avatar_cls}">{avatar_icon}</div>
        <div class="bubble {bubble_cls}">{safe_content}</div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

    # Source chunks toggle (only for assistant messages)
    if not is_user and sources and st.session_state.show_sources:
        with st.expander(f"📚 {len(sources)} source chunk(s)", expanded=False):
            for i, chunk in enumerate(sources, 1):
                page     = chunk.get("page", "?")
                pdf      = chunk.get("pdf",  chunk.get("source", "unknown"))
                text     = chunk.get("text", chunk.get("content", ""))
                score    = chunk.get("score", chunk.get("similarity", None))
                score_str = f" · score {score:.2f}" if score is not None else ""
                st.markdown(
                    f"""<div class="source-chunk">
                        <div class="chunk-header">📄 {pdf} — page {page}{score_str}</div>
                        <div class="chunk-text">{text[:400]}{'…' if len(text) > 400 else ''}</div>
                    </div>""",
                    unsafe_allow_html=True,
                )


def _render_chat_history() -> None:
    """Re-render every message in st.session_state.messages."""
    for msg in st.session_state.messages:
        _render_bubble(msg["role"], msg["content"], msg.get("sources"))


def _render_quiz(questions: list[dict]) -> None:
    """Render radio-button quiz cards with reveal-answer functionality."""
    if not questions:
        st.info("No quiz questions loaded yet.")
        return

    for idx, q in enumerate(questions):
        question    = q.get("question", f"Question {idx+1}")
        choices     = q.get("choices", q.get("options", []))
        answer      = q.get("answer", q.get("correct_answer", ""))
        explanation = q.get("explanation", "")

        st.markdown(
            f"""<div class="quiz-card">
                <div class="quiz-question">Q{idx+1}. {question}</div>
            </div>""",
            unsafe_allow_html=True,
        )

        selected = st.radio(
            label=f"q_{idx}",
            options=choices if choices else ["True", "False"],
            index=None,
            key=f"radio_{idx}",
            label_visibility="collapsed",
        )
        st.session_state.quiz_selected[idx] = selected

        col_reveal, col_next = st.columns([1, 4])
        with col_reveal:
            if st.button("Reveal ✓", key=f"reveal_{idx}"):
                st.session_state.quiz_revealed[idx] = True

        if st.session_state.quiz_revealed.get(idx):
            st.markdown(
                f'<div class="quiz-correct">✅ Correct answer: <strong>{answer}</strong></div>',
                unsafe_allow_html=True,
            )
            if explanation:
                st.markdown(
                    f'<div class="quiz-explanation">💡 {explanation}</div>',
                    unsafe_allow_html=True,
                )

        st.markdown("---")


# ──────────────────────────────────────────────
# Sidebar
# ──────────────────────────────────────────────

def _render_sidebar(pdfs: list[str]) -> None:
    with st.sidebar:
        st.markdown("## 📖 Study Panel")

        # ── Backend health ──
        healthy = api_health()
        dot     = "online" if healthy else "offline"
        label   = "Backend online" if healthy else "Backend offline"
        st.markdown(
            f'<span class="status-dot {dot}"></span>{label}',
            unsafe_allow_html=True,
        )
        st.markdown("---")

        # ── Session info ──
        st.markdown("### Session")
        short_id = st.session_state.session_id[:8] + "…"
        st.markdown(
            f'<div class="session-badge">🔑 {short_id}</div>',
            unsafe_allow_html=True,
        )

        col1, col2 = st.columns(2)
        with col1:
            if st.button("🗑 Clear chat", use_container_width=True):
                _clear_chat()
                st.rerun()
        with col2:
            if st.button("🔄 New session", use_container_width=True):
                _new_session()
                st.rerun()

        st.markdown("---")

        # ── PDF selector (global) ──
        st.markdown("### 📄 Active PDF")
        if pdfs:
            options = ["(all PDFs)"] + pdfs
            sel = st.selectbox(
                "Filter answers to:",
                options,
                index=0,
                label_visibility="collapsed",
            )
            st.session_state.selected_pdf = None if sel == "(all PDFs)" else sel
        else:
            st.caption("No PDFs found on the server.")

        # ── Source chunks toggle ──
        st.markdown("---")
        st.markdown("### ⚙️ Options")
        st.session_state.show_sources = st.toggle(
            "Show source chunks",
            value=st.session_state.show_sources,
        )

        st.markdown("---")
        st.caption("Module 4 · Student Panel")


# ──────────────────────────────────────────────
# Tab: Chat
# ──────────────────────────────────────────────

def _tab_chat() -> None:
    st.markdown("#### 💬 Ask questions about your study material")

    # Scrollable chat history area
    history_placeholder = st.container()
    with history_placeholder:
        _render_chat_history()

    st.markdown("---")

    # Input row
    with st.form(key="chat_form", clear_on_submit=True):
        col_input, col_send = st.columns([6, 1])
        with col_input:
            user_input = st.text_input(
                "Your question",
                placeholder="e.g. Explain the concept of gradient descent…",
                label_visibility="collapsed",
            )
        with col_send:
            submitted = st.form_submit_button("Send →", use_container_width=True)

    if submitted and user_input.strip():
        question = user_input.strip()

        # Append user message immediately
        st.session_state.messages.append(
            {"role": "user", "content": question, "sources": []}
        )

        with st.spinner("Thinking…"):
            result = api_ask(
                question=question,
                session_id=st.session_state.session_id,
                pdf_name=st.session_state.selected_pdf,
            )

        answer  = result.get("answer", "No answer returned.")
        sources = result.get("sources", [])

        st.session_state.messages.append(
            {"role": "assistant", "content": answer, "sources": sources}
        )
        st.rerun()

    # Empty state hint
    if not st.session_state.messages:
        st.markdown(
            '<div class="info-box">👋 Ask any question about your uploaded PDFs to get started.</div>',
            unsafe_allow_html=True,
        )


# ──────────────────────────────────────────────
# Tab: PDF Viewer
# ──────────────────────────────────────────────

def _tab_pdf_viewer(pdfs: list[str]) -> None:
    st.markdown("#### 📑 PDF Viewer")

    if not pdfs:
        st.markdown(
            '<div class="warn-box">⚠️ No PDFs are available on the server. Upload some via the backend first.</div>',
            unsafe_allow_html=True,
        )
        return

    selected = st.selectbox(
        "Select a PDF to view:",
        options=pdfs,
        index=pdfs.index(st.session_state.selected_pdf)
        if st.session_state.selected_pdf in pdfs
        else 0,
        key="pdf_viewer_dropdown",
    )
    st.session_state.selected_pdf = selected

    if selected:
        pdf_url = api_get_pdf_url(selected)
        st.markdown(
            f'<iframe src="{pdf_url}" class="pdf-frame"></iframe>',
            unsafe_allow_html=True,
        )
        st.caption(f"Viewing: **{selected}** · [Open in new tab]({pdf_url})")


# ──────────────────────────────────────────────
# Tab: Quiz
# ──────────────────────────────────────────────

def _tab_quiz(pdfs: list[str]) -> None:
    st.markdown("#### 🧠 Quiz Generator")

    if not pdfs:
        st.markdown(
            '<div class="warn-box">⚠️ No PDFs available to generate a quiz from.</div>',
            unsafe_allow_html=True,
        )
        return

    # ── Quiz config form ──
    with st.form("quiz_form"):
        col1, col2, col3 = st.columns([3, 2, 2])
        with col1:
            quiz_pdf = st.selectbox(
                "Generate quiz from:",
                options=pdfs,
                index=pdfs.index(st.session_state.selected_pdf)
                if st.session_state.selected_pdf in pdfs
                else 0,
            )
        with col2:
            num_q = st.number_input(
                "Number of questions",
                min_value=1,
                max_value=20,
                value=5,
                step=1,
            )
        with col3:
            topic = st.text_input(
                "Topic filter (optional)",
                placeholder="e.g. neural networks",
            )

        generate = st.form_submit_button("⚡ Generate Quiz", use_container_width=True)

    if generate:
        with st.spinner(f"Generating {num_q} questions from {quiz_pdf}…"):
            questions = api_quiz(
                pdf_name=quiz_pdf,
                num_questions=int(num_q),
                topic=topic.strip() or None,
            )
        st.session_state.quiz_data     = questions
        st.session_state.quiz_revealed = {}
        st.session_state.quiz_selected = {}

        if questions:
            st.success(f"✅ {len(questions)} question(s) generated!")
        else:
            st.warning("No questions were returned. Try a different PDF or topic.")

    # ── Reset button ──
    if st.session_state.quiz_data:
        if st.button("🔄 Reset quiz"):
            st.session_state.quiz_revealed = {}
            st.session_state.quiz_selected = {}
            st.rerun()

    # ── Render questions ──
    _render_quiz(st.session_state.quiz_data)


# ──────────────────────────────────────────────
# Main Entry Point  →  show_student()
# ──────────────────────────────────────────────

def show_student() -> None:
    """
    Main rendering function for the Student Panel.
    Call this from your top-level app.py dispatcher, e.g.:

        if st.session_state.role == "student":
            show_student()
    """
    # ── Page config (call only once at top-level if needed) ──
    # st.set_page_config(page_title="Study Panel", page_icon="📖", layout="wide")

    # ── Inject CSS ──
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

    # ── Init state ──
    _init_session()

    # ── Fetch PDF list (once per interaction cycle) ──
    pdfs: list[str] = api_list_pdfs()

    # ── Sidebar ──
    _render_sidebar(pdfs)

    # ── Page header ──
    st.markdown(
        """
        <div class="student-header">
            <div style="font-size:2.2rem">📖</div>
            <div>
                <h1>Study Panel</h1>
                <p>Chat with your PDFs · Take quizzes · View documents</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── Tabs ──
    tab_chat, tab_pdf, tab_quiz = st.tabs(["💬 Chat", "📄 PDF Viewer", "🧠 Quiz"])

    with tab_chat:
        _tab_chat()

    with tab_pdf:
        _tab_pdf_viewer(pdfs)

    with tab_quiz:
        _tab_quiz(pdfs)


# ──────────────────────────────────────────────
# Standalone runner (dev only)
# ──────────────────────────────────────────────

if __name__ == "__main__":
    st.set_page_config(
        page_title="Study Panel — Module 4",
        page_icon="📖",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    show_student()
