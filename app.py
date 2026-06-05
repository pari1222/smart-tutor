"""
AI Tutor — Streamlit Frontend
Two roles:
  - Admin  : upload PDFs, view uploaded docs, delete docs
  - Student: view PDFs, ask questions via RAG, take quizzes

Running `streamlit run app.py` auto-starts the FastAPI backend.
"""

import uuid, time, subprocess, sys, os, base64, requests
import streamlit as st
from pathlib import Path

# ─────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────
API_BASE_URL  = "http://localhost:8000"
BACKEND_DIR   = Path(__file__).parent.parent / "backend"

# Hardcoded credentials (swap for a DB in production)
CREDENTIALS = {
    "admin":   {"password": "admin123",   "role": "admin"},
    "student": {"password": "student123", "role": "student"},
}

# ─────────────────────────────────────────────
# Auto-start FastAPI backend ONCE at import time
# Runs before any Streamlit code so it never
# triggers a rerun loop.
# ─────────────────────────────────────────────
def _start_backend_once():
    """Start uvicorn in the background if not already running."""
    try:
        requests.get(f"{API_BASE_URL}/health", timeout=2)
        return  # already up
    except Exception:
        pass

    subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "main:app",
         "--host", "0.0.0.0", "--port", "8000"],
        cwd=str(BACKEND_DIR),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
    )
    # Block here (not in Streamlit context) until ready — max 12 seconds
    for _ in range(24):
        time.sleep(0.5)
        try:
            requests.get(f"{API_BASE_URL}/health", timeout=1)
            return
        except Exception:
            continue

# Use a module-level flag so this runs exactly once per Python process,
# not on every Streamlit rerun.
if not os.environ.get("_AI_TUTOR_BACKEND_STARTED"):
    _start_backend_once()
    os.environ["_AI_TUTOR_BACKEND_STARTED"] = "1"

# ─────────────────────────────────────────────
# Page config — must be first Streamlit call
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="AI Tutor",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
# Session state defaults
# ─────────────────────────────────────────────
for key, val in {
    "logged_in":   False,
    "role":        None,
    "username":    None,
    "session_id":  str(uuid.uuid4()),
    "chat_history": [],
    "quiz_data":   None,
    "show_sources": False,
}.items():
    if key not in st.session_state:
        st.session_state[key] = val

# ─────────────────────────────────────────────
# Global CSS
# ─────────────────────────────────────────────
st.markdown("""
<style>
/* ── Login card ── */
.login-box {
    max-width: 420px;
    margin: 60px auto;
    padding: 40px;
    border-radius: 16px;
    background: white;
    box-shadow: 0 4px 24px rgba(0,0,0,0.10);
}
/* ── Chat bubbles ── */
.user-bubble {
    background: #0078D4;
    color: white;
    padding: 10px 16px;
    border-radius: 18px 18px 4px 18px;
    margin: 6px 0 6px auto;
    max-width: 75%;
    word-wrap: break-word;
}
.assistant-bubble {
    background: #F0F2F6;
    color: #1a1a1a;
    padding: 10px 16px;
    border-radius: 18px 18px 18px 4px;
    margin: 6px auto 6px 0;
    max-width: 75%;
    word-wrap: break-word;
}
.source-box {
    background: #FFF8E1;
    border-left: 3px solid #FFC107;
    padding: 8px 12px;
    border-radius: 4px;
    font-size: 0.8em;
    color: #555;
    margin-top: 4px;
}
/* ── Role badge ── */
.badge-admin   { background:#D32F2F; color:white; padding:3px 10px;
                 border-radius:12px; font-size:0.8em; font-weight:bold; }
.badge-student { background:#1565C0; color:white; padding:3px 10px;
                 border-radius:12px; font-size:0.8em; font-weight:bold; }
/* ── PDF card ── */
.pdf-card {
    background: white;
    border: 1px solid #e0e0e0;
    border-radius: 10px;
    padding: 14px 18px;
    margin: 8px 0;
    display: flex;
    align-items: center;
    gap: 12px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.06);
}
/* ── Sidebar section header ── */
.sidebar-section {
    font-size: 0.7em;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: #888;
    margin: 16px 0 6px 0;
}
/* ── Doc pill in sidebar ── */
.doc-pill {
    display: flex;
    align-items: center;
    gap: 8px;
    background: rgba(0,120,212,0.08);
    border: 1px solid rgba(0,120,212,0.18);
    border-radius: 8px;
    padding: 6px 10px;
    margin: 4px 0;
    font-size: 0.82em;
    color: #cdd5e0;
    word-break: break-all;
}
.doc-pill span.dot {
    width: 7px; height: 7px;
    border-radius: 50%;
    background: #0078D4;
    flex-shrink: 0;
}
/* ── Status chip ── */
.status-online {
    display:inline-flex; align-items:center; gap:6px;
    background:#0d3320; color:#4caf7d;
    border:1px solid #1e5c3a;
    border-radius:20px; padding:4px 12px;
    font-size:0.78em; font-weight:600;
}
.status-offline {
    display:inline-flex; align-items:center; gap:6px;
    background:#3a0d0d; color:#f07070;
    border:1px solid #5c1e1e;
    border-radius:20px; padding:4px 12px;
    font-size:0.78em; font-weight:600;
}
.pulse { width:8px; height:8px; border-radius:50%; background:#4caf7d; }
.pulse-off { width:8px; height:8px; border-radius:50%; background:#f07070; }
/* ── User profile block ── */
.profile-block {
    display:flex; align-items:center; gap:12px;
    background:rgba(255,255,255,0.04);
    border:1px solid rgba(255,255,255,0.08);
    border-radius:12px;
    padding:12px 14px;
    margin-bottom:4px;
}
.avatar {
    width:38px; height:38px; border-radius:50%;
    background: linear-gradient(135deg,#0078D4,#00b4d8);
    display:flex; align-items:center; justify-content:center;
    font-size:1.1em; font-weight:700; color:white; flex-shrink:0;
}
.profile-name { font-weight:600; font-size:0.92em; color:#e8eaf0; }
.profile-role { font-size:0.73em; color:#8892a4; margin-top:1px; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# API helpers
# ─────────────────────────────────────────────
@st.cache_data(ttl=10)
def api_health() -> bool:
    """Check backend health — cached for 10 seconds to avoid rerun loops."""
    try:
        return requests.get(f"{API_BASE_URL}/health", timeout=3).status_code == 200
    except Exception:
        return False

def api_upload(file_bytes: bytes, filename: str) -> dict:
    resp = requests.post(f"{API_BASE_URL}/upload",
                         files={"file": (filename, file_bytes, "application/pdf")},
                         timeout=120)
    resp.raise_for_status()
    return resp.json()

def api_list_pdfs() -> list:
    try:
        resp = requests.get(f"{API_BASE_URL}/documents/list", timeout=5)
        resp.raise_for_status()
        data = resp.json()
        # support both {"documents": [...]} and {"files": [...]}
        return data.get("documents", data.get("files", []))
    except Exception:
        return []

def api_delete_pdf(filename: str) -> dict:
    resp = requests.delete(f"{API_BASE_URL}/documents/{filename}", timeout=10)
    resp.raise_for_status()
    return resp.json()

def api_ask(question: str, session_id: str) -> dict:
    resp = requests.post(f"{API_BASE_URL}/ask",
                         json={"question": question, "session_id": session_id},
                         timeout=60)
    resp.raise_for_status()
    return resp.json()

def api_quiz(topic: str, num_q: int) -> dict:
    resp = requests.post(f"{API_BASE_URL}/quiz",
                         json={"topic": topic, "num_questions": num_q},
                         timeout=60)
    resp.raise_for_status()
    data = resp.json()
    # Normalise to {"topic": ..., "questions": [...]}
    return {
        "topic": topic,
        "questions": data.get("questions", data if isinstance(data, list) else [])
    }

def api_clear_session(session_id: str):
    try:
        requests.delete(f"{API_BASE_URL}/session/{session_id}", timeout=5)
    except Exception:
        pass

def get_pdf_url(filename: str) -> str:
    """Return the URL to stream a PDF from the backend static mount."""
    return f"{API_BASE_URL}/pdfs/{requests.utils.quote(filename)}"

def pdf_to_base64(filename: str) -> str | None:
    """Fetch PDF bytes and encode as base64 for inline iframe display."""
    try:
        resp = requests.get(get_pdf_url(filename), timeout=15)
        resp.raise_for_status()
        return base64.b64encode(resp.content).decode("utf-8")
    except Exception:
        return None

# ─────────────────────────────────────────────
# LOGIN PAGE
# ─────────────────────────────────────────────
def show_login():
    st.markdown("""
    <div style='text-align:center; margin-top:40px;'>
        <h1>🎓 AI Tutor Platform</h1>
        <p style='color:#666;'>Sign in to continue</p>
    </div>
    """, unsafe_allow_html=True)

    col_l, col_m, col_r = st.columns([1, 1.2, 1])
    with col_m:
        with st.form("login_form"):
            st.subheader("Sign In")
            username = st.text_input("Username", placeholder="admin or student")
            password = st.text_input("Password", type="password", placeholder="••••••••")
            submitted = st.form_submit_button("Login →", use_container_width=True, type="primary")

        if submitted:
            user = CREDENTIALS.get(username.strip().lower())
            if user and user["password"] == password:
                st.session_state.logged_in = True
                st.session_state.role      = user["role"]
                st.session_state.username  = username.strip().lower()
                st.rerun()
            else:
                st.error("Invalid username or password.")

        st.divider()
        st.caption("**Demo credentials**")
        st.caption("Admin → username: `admin` | password: `admin123`")
        st.caption("Student → username: `student` | password: `student123`")

# ─────────────────────────────────────────────
# SHARED SIDEBAR
# ─────────────────────────────────────────────
def render_sidebar():
    with st.sidebar:
        st.markdown(f"""
        <div style='margin-bottom:8px;'>
            <span style='font-size:1.3em; font-weight:bold;'>🎓 AI Tutor</span><br/>
            <span class='badge-{"admin" if st.session_state.role=="admin" else "student"}'>
                {"👑 Admin" if st.session_state.role=="admin" else "🧑‍🎓 Student"}
            </span>
            &nbsp; <span style='color:#888; font-size:0.9em;'>{st.session_state.username}</span>
        </div>
        """, unsafe_allow_html=True)

        # Backend status (admin only — students get their own styled chip)
        if st.session_state.role == "admin":
            if api_health():
                st.success("Backend online", icon="🟢")
            else:
                st.error("Backend offline", icon="🔴")

            st.divider()

            if st.button("🚪 Logout", use_container_width=True):
                for key in ["logged_in", "role", "username", "chat_history",
                            "quiz_data", "session_id"]:
                    st.session_state[key] = None if key in ["role","username"] else \
                                            False if key == "logged_in" else \
                                            [] if key == "chat_history" else \
                                            str(uuid.uuid4()) if key == "session_id" else None
                st.rerun()

# ─────────────────────────────────────────────
# ADMIN DASHBOARD
# ─────────────────────────────────────────────
def show_admin():
    render_sidebar()

    st.title("👑 Admin Dashboard")
    st.caption("Upload syllabus PDFs and manage course materials.")

    tab_upload, tab_manage = st.tabs(["📤 Upload PDF", "📂 Manage PDFs"])

    # ── Upload Tab ──────────────────────────────
    with tab_upload:
        st.subheader("Upload New Syllabus PDF")
        st.info("Uploaded PDFs are processed into the AI knowledge base AND stored for student viewing.", icon="ℹ️")

        uploaded = st.file_uploader(
            "Choose PDF file(s)",
            type=["pdf"],
            accept_multiple_files=True,
            help="You can upload multiple PDFs at once.",
        )

        if uploaded:
            if st.button("⬆️ Process & Upload All", type="primary"):
                for f in uploaded:
                    with st.spinner(f"Processing `{f.name}`..."):
                        try:
                            result = api_upload(f.read(), f.name)
                            st.success(
                                f"✅ **{f.name}** — {result['chunks_created']} chunks created.",
                                icon="📚"
                            )
                        except requests.HTTPError as e:
                            st.error(f"❌ {f.name}: {e.response.json().get('detail', str(e))}")
                        except Exception as e:
                            st.error(f"❌ {f.name}: {str(e)}")

    # ── Manage Tab ──────────────────────────────
    with tab_manage:
        st.subheader("Uploaded Documents")

        pdf_list = api_list_pdfs()

        if not pdf_list:
            st.info("No PDFs uploaded yet. Go to the Upload tab to add some.", icon="📄")
        else:
            st.caption(f"{len(pdf_list)} document(s) in the knowledge base")
            st.divider()

            for fname in pdf_list:
                col_icon, col_name, col_view, col_del = st.columns([0.5, 4, 1.5, 1.5])
                with col_icon:
                    st.markdown("📄")
                with col_name:
                    st.markdown(f"**{fname}**")
                with col_view:
                    if st.button("👁️ Preview", key=f"prev_{fname}", use_container_width=True):
                        st.session_state[f"preview_{fname}"] = not st.session_state.get(f"preview_{fname}", False)
                with col_del:
                    if st.button("🗑️ Delete", key=f"del_{fname}", use_container_width=True):
                        try:
                            api_delete_pdf(fname)
                            st.success(f"Deleted `{fname}`")
                            st.rerun()
                        except Exception as e:
                            st.error(str(e))

                # Inline PDF preview
                if st.session_state.get(f"preview_{fname}", False):
                    with st.expander(f"📖 {fname}", expanded=True):
                        b64 = pdf_to_base64(fname)
                        if b64:
                            st.markdown(
                                f'<iframe src="data:application/pdf;base64,{b64}" '
                                f'width="100%" height="700px" style="border:none; border-radius:8px;"></iframe>',
                                unsafe_allow_html=True,
                            )
                        else:
                            st.error("Could not load PDF preview.")

                st.divider()

# ─────────────────────────────────────────────
# STUDENT DASHBOARD
# ─────────────────────────────────────────────
def show_student():
    render_sidebar()

    # ── Student Sidebar ──────────────────────────
    with st.sidebar:

        # 1. Profile block
        uname = st.session_state.username or "student"
        avatar_letter = uname[0].upper()
        st.markdown(f"""
        <div class="profile-block">
            <div class="avatar">{avatar_letter}</div>
            <div>
                <div class="profile-name">{uname}</div>
                <div class="profile-role">🧑‍🎓 Student</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # 2. Backend status chip
        if api_health():
            st.markdown(
                '<div class="status-online"><span class="pulse"></span>Backend Online</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                '<div class="status-offline"><span class="pulse-off"></span>Backend Offline</div>',
                unsafe_allow_html=True,
            )

        st.markdown("<div style='margin:10px 0'></div>", unsafe_allow_html=True)

        # 3. Available Documents
        st.markdown('<div class="sidebar-section">📚 Available Documents</div>', unsafe_allow_html=True)
        pdf_list = api_list_pdfs()
        if pdf_list:
            for fname in pdf_list:
                short = fname if len(fname) <= 28 else fname[:25] + "..."
                st.markdown(
                    f'<div class="doc-pill"><span class="dot"></span>{short}</div>',
                    unsafe_allow_html=True,
                )
        else:
            st.caption("No documents uploaded yet.")

        st.divider()

        # 4. Quiz Generator
        st.markdown('<div class="sidebar-section">🧠 Quiz Generator</div>', unsafe_allow_html=True)
        quiz_topic = st.text_input(
            "Topic",
            placeholder="e.g. TCP/IP, OSI Model...",
            label_visibility="collapsed",
            key="quiz_topic_input",
        )
        num_q = st.slider("Number of Questions", min_value=3, max_value=10, value=5)

        if st.button("⚡ Generate Quiz", use_container_width=True, type="primary"):
            if not quiz_topic.strip():
                st.warning("Enter a topic first.")
            else:
                with st.spinner("Generating quiz..."):
                    try:
                        st.session_state.quiz_data = api_quiz(quiz_topic.strip(), num_q)
                        st.success(f"✅ {len(st.session_state.quiz_data['questions'])} questions ready!")
                    except requests.HTTPError as e:
                        st.error(e.response.json().get("detail", str(e)))
                    except Exception as e:
                        st.error(str(e))

        st.divider()

        # 5. Chat Options
        st.markdown('<div class="sidebar-section">⚙️ Chat Options</div>', unsafe_allow_html=True)
        st.session_state.show_sources = st.toggle(
            "Show source chunks",
            value=st.session_state.show_sources,
        )

        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("🗑️ Clear Chat", use_container_width=True):
                api_clear_session(st.session_state.session_id)
                st.session_state.chat_history = []
                st.session_state.session_id   = str(uuid.uuid4())
                st.session_state.quiz_data    = None
                st.rerun()
        with col_b:
            if st.button("🚪 Logout", use_container_width=True):
                for key in ["logged_in", "role", "username", "chat_history", "quiz_data", "session_id"]:
                    st.session_state[key] = (
                        None  if key in ["role", "username"] else
                        False if key == "logged_in" else
                        []    if key == "chat_history" else
                        str(uuid.uuid4()) if key == "session_id" else
                        None
                    )
                st.rerun()

        # 6. Session info at bottom
        st.markdown("<div style='margin-top:auto'></div>", unsafe_allow_html=True)
        st.caption(f"Session: `{st.session_state.session_id[:8]}...`")

    # ── Main content ─────────────────────────────
    st.title("🧑‍🎓 Student Portal")

    tab_chat, tab_pdfs, tab_quiz = st.tabs(["💬 Ask AI Tutor", "📄 View Syllabus", "📝 Quiz"])

    # ── Chat Tab ────────────────────────────────
    with tab_chat:
        st.subheader("Ask Your AI Tutor")
        st.caption("Questions are answered strictly from uploaded syllabus documents.")

        if not pdf_list:
            st.warning("No syllabus uploaded yet. Ask your admin to upload course materials.", icon="📄")

        # Render chat history
        for msg in st.session_state.chat_history:
            if msg["role"] == "user":
                st.markdown(
                    f'<div class="user-bubble">🧑‍🎓 {msg["content"]}</div>',
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    f'<div class="assistant-bubble">🤖 {msg["content"]}</div>',
                    unsafe_allow_html=True,
                )
                if st.session_state.show_sources and msg.get("sources"):
                    with st.expander("📖 Sources used", expanded=False):
                        for i, src in enumerate(msg["sources"], 1):
                            st.markdown(
                                f'<div class="source-box"><b>Source {i}:</b> {src}</div>',
                                unsafe_allow_html=True,
                            )

        st.divider()
        with st.form("chat_form", clear_on_submit=True):
            col1, col2 = st.columns([5, 1])
            with col1:
                user_input = st.text_input(
                    "question", label_visibility="collapsed",
                    placeholder="Ask anything from your syllabus...",
                )
            with col2:
                send = st.form_submit_button("Send ➤", use_container_width=True, type="primary")

        if send and user_input.strip():
            st.session_state.chat_history.append(
                {"role": "user", "content": user_input.strip(), "sources": []}
            )
            with st.spinner("Thinking..."):
                try:
                    result = api_ask(user_input.strip(), st.session_state.session_id)
                    st.session_state.chat_history.append({
                        "role": "assistant",
                        "content": result["answer"],
                        "sources": result.get("sources", []),
                    })
                except requests.HTTPError as e:
                    st.session_state.chat_history.append({
                        "role": "assistant",
                        "content": f"⚠️ {e.response.json().get('detail', str(e))}",
                        "sources": [],
                    })
                except Exception as e:
                    st.session_state.chat_history.append({
                        "role": "assistant",
                        "content": f"⚠️ Could not reach backend: {str(e)}",
                        "sources": [],
                    })
            st.rerun()

    # ── PDF Viewer Tab ───────────────────────────
    with tab_pdfs:
        st.subheader("📄 Course Materials")

        if not pdf_list:
            st.info("No documents available yet. Your admin hasn't uploaded any PDFs.", icon="📚")
        else:
            selected_pdf = st.selectbox(
                "Select a document to view",
                options=pdf_list,
                format_func=lambda x: f"📄 {x}",
            )

            if selected_pdf:
                st.caption(f"Viewing: **{selected_pdf}**")
                with st.spinner("Loading PDF..."):
                    b64 = pdf_to_base64(selected_pdf)
                if b64:
                    st.markdown(
                        f'<iframe src="data:application/pdf;base64,{b64}" '
                        f'width="100%" height="800px" '
                        f'style="border:1px solid #e0e0e0; border-radius:8px;"></iframe>',
                        unsafe_allow_html=True,
                    )
                else:
                    st.error("Could not load the PDF. Please try again.")

    # ── Quiz Tab ─────────────────────────────────
    with tab_quiz:
        st.subheader("📝 Practice Quiz")

        if st.session_state.quiz_data is None:
            st.info("👈 Enter a topic in the sidebar and click '⚡ Generate Quiz'.", icon="🎯")
        else:
            quiz = st.session_state.quiz_data
            st.markdown(f"**Topic:** {quiz['topic']}  |  **{len(quiz['questions'])} questions**")
            st.divider()

            for i, q in enumerate(quiz["questions"], 1):
                st.markdown(f"**Q{i}. {q['question']}**")
                selected = st.radio(
                    f"q{i}", options=q["options"],
                    key=f"quiz_q_{i}", label_visibility="collapsed",
                )
                if st.button("Reveal Answer", key=f"reveal_{i}"):
                    if selected == q["answer"]:
                        st.success(f"✅ Correct! → **{q['answer']}**")
                    else:
                        st.error(f"❌ Wrong. You chose: **{selected}**\n\nCorrect: **{q['answer']}**")
                st.markdown("---")

            if st.button("🔄 New Quiz", type="secondary"):
                st.session_state.quiz_data = None
                st.rerun()

# ─────────────────────────────────────────────
# ROUTER — show correct page based on auth state
# ─────────────────────────────────────────────
if not st.session_state.logged_in:
    show_login()
elif st.session_state.role == "admin":
    show_admin()
else:
    show_student()
