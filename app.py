"""
AI Tutor — Streamlit Frontend  v3.0
New features:
  - Text-to-Speech for AI answers (browser Web Speech API)
  - Student Progress Tracker with bar chart
  - Ask Doubt to Admin (student submits, admin replies)
  - Weekly Exam Schedule (admin sets, student sees countdown)
"""

import uuid, time, subprocess, sys, os, base64, requests, json
from datetime import datetime, date
import streamlit as st
from pathlib import Path

# ─────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────
API_BASE_URL = "http://localhost:8000"
BACKEND_DIR  = Path(__file__).parent.parent / "backend"

CREDENTIALS = {
    "admin":   {"password": "admin123",   "role": "admin"},
    "student": {"password": "student123", "role": "student"},
}

# ─────────────────────────────────────────────
# Auto-start backend once
# ─────────────────────────────────────────────
def _start_backend_once():
    try:
        requests.get(f"{API_BASE_URL}/health", timeout=2)
        return
    except Exception:
        pass
    subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"],
        cwd=str(BACKEND_DIR),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
    )
    for _ in range(24):
        time.sleep(0.5)
        try:
            requests.get(f"{API_BASE_URL}/health", timeout=1)
            return
        except Exception:
            continue

if not os.environ.get("_AI_TUTOR_BACKEND_STARTED"):
    _start_backend_once()
    os.environ["_AI_TUTOR_BACKEND_STARTED"] = "1"

# ─────────────────────────────────────────────
# Page config
# ─────────────────────────────────────────────
st.set_page_config(page_title="AI Tutor", page_icon="🎓", layout="wide",
                   initial_sidebar_state="expanded")

# ─────────────────────────────────────────────
# Session state
# ─────────────────────────────────────────────
_defaults = {
    "logged_in":    False,
    "role":         None,
    "username":     None,
    "session_id":   str(uuid.uuid4()),
    "chat_history": [],
    "quiz_data":    None,
    "show_sources": False,
    "quiz_answers": {},       # {q_index: selected_option}
    "quiz_revealed":{},       # {q_index: bool}
    "quiz_submitted": False,  # whether score was saved this session
}
for k, v in _defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ─────────────────────────────────────────────
# CSS
# ─────────────────────────────────────────────
st.markdown("""
<style>
.user-bubble {
    background:#0078D4; color:white;
    padding:10px 16px; border-radius:18px 18px 4px 18px;
    margin:6px 0 6px auto; max-width:75%; word-wrap:break-word;
}
.assistant-bubble {
    background:#F0F2F6; color:#1a1a1a;
    padding:10px 16px; border-radius:18px 18px 18px 4px;
    margin:6px auto 6px 0; max-width:75%; word-wrap:break-word;
}
.source-box {
    background:#FFF8E1; border-left:3px solid #FFC107;
    padding:8px 12px; border-radius:4px;
    font-size:0.8em; color:#555; margin-top:4px;
}
.badge-admin   {background:#D32F2F;color:white;padding:3px 10px;border-radius:12px;font-size:0.8em;font-weight:bold;}
.badge-student {background:#1565C0;color:white;padding:3px 10px;border-radius:12px;font-size:0.8em;font-weight:bold;}
.sidebar-section {
    font-size:0.7em; font-weight:700; letter-spacing:0.08em;
    text-transform:uppercase; color:#888; margin:16px 0 6px 0;
}
.doc-pill {
    display:flex; align-items:center; gap:8px;
    background:rgba(0,120,212,0.08); border:1px solid rgba(0,120,212,0.18);
    border-radius:8px; padding:6px 10px; margin:4px 0;
    font-size:0.82em; color:#cdd5e0; word-break:break-all;
}
.doc-pill span.dot {width:7px;height:7px;border-radius:50%;background:#0078D4;flex-shrink:0;}
.status-online  {display:inline-flex;align-items:center;gap:6px;background:#0d3320;color:#4caf7d;border:1px solid #1e5c3a;border-radius:20px;padding:4px 12px;font-size:0.78em;font-weight:600;}
.status-offline {display:inline-flex;align-items:center;gap:6px;background:#3a0d0d;color:#f07070;border:1px solid #5c1e1e;border-radius:20px;padding:4px 12px;font-size:0.78em;font-weight:600;}
.pulse     {width:8px;height:8px;border-radius:50%;background:#4caf7d;}
.pulse-off {width:8px;height:8px;border-radius:50%;background:#f07070;}
.profile-block {
    display:flex;align-items:center;gap:12px;
    background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.08);
    border-radius:12px;padding:12px 14px;margin-bottom:4px;
}
.avatar {
    width:38px;height:38px;border-radius:50%;
    background:linear-gradient(135deg,#0078D4,#00b4d8);
    display:flex;align-items:center;justify-content:center;
    font-size:1.1em;font-weight:700;color:white;flex-shrink:0;
}
.profile-name {font-weight:600;font-size:0.92em;color:#e8eaf0;}
.profile-role {font-size:0.73em;color:#8892a4;margin-top:1px;}
.exam-card {
    background:rgba(255,193,7,0.07);border:1px solid rgba(255,193,7,0.25);
    border-radius:12px;padding:14px 18px;margin:8px 0;
}
.exam-card-urgent {
    background:rgba(244,67,54,0.08);border:1px solid rgba(244,67,54,0.3);
    border-radius:12px;padding:14px 18px;margin:8px 0;
}
.doubt-card {
    background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.1);
    border-radius:10px;padding:14px;margin:8px 0;
}
.doubt-reply {
    background:rgba(0,120,212,0.1);border-left:3px solid #0078D4;
    border-radius:0 8px 8px 0;padding:10px 14px;margin-top:8px;
    font-size:0.88em;
}
.tts-btn {
    background:none;border:1px solid rgba(255,255,255,0.15);
    color:#aab;border-radius:6px;padding:2px 8px;
    font-size:0.75em;cursor:pointer;
}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# TTS helper — injects Web Speech API JS
# ─────────────────────────────────────────────
def tts_button(text: str, key: str):
    """Render a small 🔊 button that speaks the given text via browser TTS."""
    # Escape text for JS string
    safe = text.replace("\\", "\\\\").replace("`", "\\`").replace("$", "\\$")
    st.components.v1.html(f"""
    <button class="tts-btn" onclick="
        var u = new SpeechSynthesisUtterance(`{safe}`);
        u.lang = 'en-US'; u.rate = 0.95;
        window.speechSynthesis.cancel();
        window.speechSynthesis.speak(u);
    ">🔊 Listen</button>
    <button class="tts-btn" onclick="window.speechSynthesis.cancel();"
            style="margin-left:4px;">⏹ Stop</button>
    """, height=36)

# ─────────────────────────────────────────────
# API helpers
# ─────────────────────────────────────────────
@st.cache_data(ttl=10)
def api_health() -> bool:
    try:
        return requests.get(f"{API_BASE_URL}/health", timeout=3).status_code == 200
    except Exception:
        return False

def api_upload(file_bytes, filename):
    r = requests.post(f"{API_BASE_URL}/upload",
                      files={"file": (filename, file_bytes, "application/pdf")}, timeout=120)
    r.raise_for_status(); return r.json()

def api_list_pdfs():
    try:
        r = requests.get(f"{API_BASE_URL}/documents/list", timeout=5); r.raise_for_status()
        d = r.json()
        return d.get("documents", d.get("files", []))
    except Exception:
        return []

def api_delete_pdf(filename):
    r = requests.delete(f"{API_BASE_URL}/documents/{filename}", timeout=10)
    r.raise_for_status(); return r.json()

def api_ask(question, session_id):
    r = requests.post(f"{API_BASE_URL}/ask",
                      json={"question": question, "session_id": session_id}, timeout=60)
    r.raise_for_status(); return r.json()

def api_quiz(topic, num_q):
    r = requests.post(f"{API_BASE_URL}/quiz",
                      json={"topic": topic, "num_questions": num_q}, timeout=60)
    r.raise_for_status()
    d = r.json()
    return {"topic": topic, "questions": d.get("questions", d if isinstance(d, list) else [])}

def api_clear_session(session_id):
    try: requests.delete(f"{API_BASE_URL}/session/{session_id}", timeout=5)
    except Exception: pass

def pdf_to_base64(filename):
    try:
        r = requests.get(f"{API_BASE_URL}/pdfs/{requests.utils.quote(filename)}", timeout=15)
        r.raise_for_status()
        return base64.b64encode(r.content).decode("utf-8")
    except Exception:
        return None

# ── Progress / Scores ────────────────────────
def api_save_score(student, topic, correct, total, session_id):
    try:
        r = requests.post(f"{API_BASE_URL}/scores",
                          json={"student": student, "topic": topic,
                                "correct": correct, "total": total,
                                "session_id": session_id}, timeout=10)
        r.raise_for_status()
    except Exception as e:
        st.warning(f"Could not save score: {e}")

def api_get_scores(student):
    try:
        r = requests.get(f"{API_BASE_URL}/scores/{student}", timeout=5)
        r.raise_for_status()
        return r.json().get("scores", [])
    except Exception:
        return []

def api_get_all_scores():
    try:
        r = requests.get(f"{API_BASE_URL}/scores", timeout=5)
        r.raise_for_status()
        return r.json().get("scores", [])
    except Exception:
        return []

# ── Doubts ───────────────────────────────────
def api_submit_doubt(student, message, topic="General"):
    r = requests.post(f"{API_BASE_URL}/doubts",
                      json={"student": student, "message": message, "topic": topic}, timeout=10)
    r.raise_for_status(); return r.json()

def api_get_all_doubts():
    try:
        r = requests.get(f"{API_BASE_URL}/doubts", timeout=5)
        r.raise_for_status()
        return r.json().get("doubts", [])
    except Exception:
        return []

def api_get_my_doubts(student):
    try:
        r = requests.get(f"{API_BASE_URL}/doubts/student/{student}", timeout=5)
        r.raise_for_status()
        return r.json().get("doubts", [])
    except Exception:
        return []

def api_reply_doubt(doubt_id, reply):
    r = requests.post(f"{API_BASE_URL}/doubts/{doubt_id}/reply",
                      json={"doubt_id": doubt_id, "reply": reply}, timeout=10)
    r.raise_for_status(); return r.json()

# ── Exams ─────────────────────────────────────
def api_schedule_exam(pdf_filename, exam_date, topic, num_questions):
    r = requests.post(f"{API_BASE_URL}/exams",
                      json={"pdf_filename": pdf_filename, "exam_date": exam_date,
                            "topic": topic, "num_questions": num_questions}, timeout=10)
    r.raise_for_status(); return r.json()

def api_get_exams():
    try:
        r = requests.get(f"{API_BASE_URL}/exams", timeout=5)
        r.raise_for_status()
        return r.json().get("exams", [])
    except Exception:
        return []

def api_delete_exam(exam_id):
    r = requests.delete(f"{API_BASE_URL}/exams/{exam_id}", timeout=10)
    r.raise_for_status(); return r.json()

# ─────────────────────────────────────────────
# LOGIN PAGE
# ─────────────────────────────────────────────
def show_login():
    st.markdown("""
    <div style='text-align:center;margin-top:40px;'>
        <h1>🎓 AI Tutor Platform</h1>
        <p style='color:#666;'>Sign in to continue</p>
    </div>""", unsafe_allow_html=True)
    _, col, _ = st.columns([1, 1.2, 1])
    with col:
        with st.form("login_form"):
            st.subheader("Sign In")
            username = st.text_input("Username", placeholder="admin or student")
            password = st.text_input("Password", type="password", placeholder="••••••••")
            sub = st.form_submit_button("Login →", use_container_width=True, type="primary")
        if sub:
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
        st.caption("Admin → `admin` / `admin123`   |   Student → `student` / `student123`")

# ─────────────────────────────────────────────
# ADMIN SIDEBAR
# ─────────────────────────────────────────────
def render_admin_sidebar():
    with st.sidebar:
        st.markdown("## 👑 AI Tutor")
        if api_health():
            st.success("Backend online", icon="🟢")
        else:
            st.error("Backend offline", icon="🔴")
        st.divider()
        if st.button("🚪 Logout", use_container_width=True):
            for k in _defaults:
                st.session_state[k] = _defaults[k]
            st.rerun()

# ─────────────────────────────────────────────
# ADMIN DASHBOARD
# ─────────────────────────────────────────────
def show_admin():
    render_admin_sidebar()
    st.title("👑 Admin Dashboard")

    tab_upload, tab_manage, tab_doubts, tab_exams, tab_progress = st.tabs([
        "📤 Upload PDF", "📂 Manage PDFs", "❓ Student Doubts",
        "📅 Exam Schedule", "📊 Student Progress"
    ])

    # ── Upload ───────────────────────────────
    with tab_upload:
        st.subheader("Upload Syllabus PDF")
        st.info("PDFs are ingested into the RAG knowledge base and made available to students.", icon="ℹ️")
        uploaded = st.file_uploader("Choose PDF(s)", type=["pdf"], accept_multiple_files=True)
        if uploaded and st.button("⬆️ Process & Upload All", type="primary"):
            for f in uploaded:
                with st.spinner(f"Processing `{f.name}`..."):
                    try:
                        result = api_upload(f.read(), f.name)
                        st.success(f"✅ **{f.name}** — {result['chunks_created']} chunks created.")
                    except Exception as e:
                        st.error(f"❌ {f.name}: {e}")

    # ── Manage ───────────────────────────────
    with tab_manage:
        st.subheader("Uploaded Documents")
        pdf_list = api_list_pdfs()
        if not pdf_list:
            st.info("No PDFs uploaded yet.", icon="📄")
        else:
            st.caption(f"{len(pdf_list)} document(s) in knowledge base")
            st.divider()
            for fname in pdf_list:
                c1, c2, c3, c4 = st.columns([0.5, 4, 1.5, 1.5])
                c1.markdown("📄")
                c2.markdown(f"**{fname}**")
                with c3:
                    if st.button("👁️ Preview", key=f"prev_{fname}", use_container_width=True):
                        st.session_state[f"preview_{fname}"] = not st.session_state.get(f"preview_{fname}", False)
                with c4:
                    if st.button("🗑️ Delete", key=f"del_{fname}", use_container_width=True):
                        try:
                            api_delete_pdf(fname)
                            st.success(f"Deleted `{fname}`")
                            st.rerun()
                        except Exception as e:
                            st.error(str(e))
                if st.session_state.get(f"preview_{fname}", False):
                    with st.expander(f"📖 {fname}", expanded=True):
                        b64 = pdf_to_base64(fname)
                        if b64:
                            st.markdown(
                                f'<iframe src="data:application/pdf;base64,{b64}" '
                                f'width="100%" height="700px" style="border:none;border-radius:8px;"></iframe>',
                                unsafe_allow_html=True)
                        else:
                            st.error("Could not load preview.")
                st.divider()

    # ── Student Doubts ───────────────────────
    with tab_doubts:
        st.subheader("❓ Student Doubts & Topic Requests")
        st.caption("Review and reply to questions students have sent to you.")

        doubts = api_get_all_doubts()
        if not doubts:
            st.info("No doubts submitted yet.", icon="✅")
        else:
            pending   = [d for d in doubts if not d.get("reply")]
            replied   = [d for d in doubts if d.get("reply")]
            st.markdown(f"**{len(pending)} pending** · {len(replied)} replied")
            st.divider()

            for d in sorted(doubts, key=lambda x: x["id"], reverse=True):
                is_pending = not d.get("reply")
                with st.container():
                    st.markdown(f"""
                    <div class="doubt-card">
                        <b>#{d['id']} — {d['student']}</b>
                        <span style='color:#888;font-size:0.8em;margin-left:8px;'>
                            {d['topic']} · {d['timestamp'][:16].replace('T',' ')}
                        </span>
                        {"<span style='background:#e65100;color:white;font-size:0.7em;padding:2px 7px;border-radius:10px;margin-left:6px;'>Pending</span>" if is_pending else ""}
                        <br/><br/>
                        💬 {d['message']}
                        {f'<div class="doubt-reply">🧑‍💼 <b>Admin:</b> {d["reply"]}<br/><span style="color:#888;font-size:0.75em;">{(d.get("replied_at") or "")[:16].replace("T"," ")}</span></div>' if d.get("reply") else ""}
                    </div>""", unsafe_allow_html=True)

                    if is_pending:
                        with st.form(f"reply_form_{d['id']}"):
                            reply_text = st.text_area("Your reply", key=f"reply_{d['id']}", height=80)
                            if st.form_submit_button("📨 Send Reply", type="primary"):
                                if reply_text.strip():
                                    try:
                                        api_reply_doubt(d["id"], reply_text.strip())
                                        st.success("Reply sent!")
                                        st.rerun()
                                    except Exception as e:
                                        st.error(str(e))
                                else:
                                    st.warning("Reply cannot be empty.")
                st.divider()

    # ── Exam Schedule ────────────────────────
    with tab_exams:
        st.subheader("📅 Schedule Weekly MCQ Exam")
        st.caption("After uploading a PDF, schedule an exam. Students will see a countdown timer.")

        pdf_list = api_list_pdfs()
        col1, col2 = st.columns(2)
        with col1:
            with st.form("schedule_exam_form"):
                st.markdown("**New Exam**")
                sel_pdf = st.selectbox("Select PDF", options=pdf_list if pdf_list else ["— upload PDFs first —"])
                exam_topic = st.text_input("Unit / Topic name", placeholder="e.g. Unit 3 — Network Layer")
                exam_date  = st.date_input("Exam Date", min_value=date.today())
                num_q      = st.slider("Number of questions", 3, 20, 10)
                if st.form_submit_button("📅 Schedule Exam", type="primary"):
                    if not pdf_list:
                        st.warning("Upload a PDF first.")
                    elif not exam_topic.strip():
                        st.warning("Enter a topic name.")
                    else:
                        try:
                            api_schedule_exam(sel_pdf, str(exam_date), exam_topic.strip(), num_q)
                            st.success(f"Exam scheduled for {exam_date}!")
                            st.rerun()
                        except Exception as e:
                            st.error(str(e))

        with col2:
            st.markdown("**Scheduled Exams**")
            exams = api_get_exams()
            if not exams:
                st.info("No exams scheduled yet.")
            else:
                for ex in sorted(exams, key=lambda x: x["exam_date"]):
                    try:
                        days_left = (date.fromisoformat(ex["exam_date"]) - date.today()).days
                    except Exception:
                        days_left = "?"
                    urgency = "exam-card-urgent" if isinstance(days_left, int) and days_left <= 3 else "exam-card"
                    st.markdown(f"""
                    <div class="{urgency}">
                        📄 <b>{ex['pdf_filename']}</b><br/>
                        📌 {ex['topic']}<br/>
                        📅 {ex['exam_date']} &nbsp;·&nbsp;
                        ⏳ {"<b style='color:#f44336'>" if urgency == "exam-card-urgent" else ""}{days_left} day{"s" if days_left != 1 else ""} left{"</b>" if urgency == "exam-card-urgent" else ""}<br/>
                        ❓ {ex['num_questions']} questions
                    </div>""", unsafe_allow_html=True)
                    if st.button("🗑️ Remove", key=f"del_exam_{ex['id']}"):
                        try:
                            api_delete_exam(ex["id"])
                            st.rerun()
                        except Exception as e:
                            st.error(str(e))

    # ── Student Progress ─────────────────────
    with tab_progress:
        st.subheader("📊 Student Progress Overview")
        all_scores = api_get_all_scores()
        if not all_scores:
            st.info("No quiz scores recorded yet.", icon="📈")
        else:
            # Group by student
            students = sorted(set(s["student"] for s in all_scores))
            sel_student = st.selectbox("Select student", options=["All"] + students)

            filtered = all_scores if sel_student == "All" else \
                       [s for s in all_scores if s["student"] == sel_student]

            # Summary metrics
            total_quizzes = len(filtered)
            avg_score     = round(sum(s["score_pct"] for s in filtered) / total_quizzes, 1) if filtered else 0
            c1, c2, c3 = st.columns(3)
            c1.metric("Total Quizzes", total_quizzes)
            c2.metric("Avg Score", f"{avg_score}%")
            best = max(filtered, key=lambda x: x["score_pct"]) if filtered else None
            c3.metric("Best Topic", best["topic"] if best else "—",
                      f"{best['score_pct']}%" if best else "")

            st.divider()

            # Bar chart — score per attempt
            import pandas as pd
            df = pd.DataFrame(filtered)
            df["label"] = df["student"] + " — " + df["topic"]
            st.bar_chart(df.set_index("label")["score_pct"])

            # Raw table
            with st.expander("📋 Raw Records"):
                st.dataframe(df[["student", "topic", "correct", "total", "score_pct", "timestamp"]],
                             use_container_width=True)

# ─────────────────────────────────────────────
# STUDENT DASHBOARD
# ─────────────────────────────────────────────
def show_student():
    # ── Student Sidebar ──────────────────────
    with st.sidebar:
        uname = st.session_state.username or "student"
        st.markdown(f"""
        <div class="profile-block">
            <div class="avatar">{uname[0].upper()}</div>
            <div>
                <div class="profile-name">{uname}</div>
                <div class="profile-role">🧑‍🎓 Student</div>
            </div>
        </div>""", unsafe_allow_html=True)

        if api_health():
            st.markdown('<div class="status-online"><span class="pulse"></span>Backend Online</div>',
                        unsafe_allow_html=True)
        else:
            st.markdown('<div class="status-offline"><span class="pulse-off"></span>Backend Offline</div>',
                        unsafe_allow_html=True)

        st.markdown("<div style='margin:10px 0'></div>", unsafe_allow_html=True)

        # Available docs
        st.markdown('<div class="sidebar-section">📚 Available Documents</div>', unsafe_allow_html=True)
        pdf_list = api_list_pdfs()
        if pdf_list:
            for fname in pdf_list:
                short = fname if len(fname) <= 28 else fname[:25] + "..."
                st.markdown(f'<div class="doc-pill"><span class="dot"></span>{short}</div>',
                            unsafe_allow_html=True)
        else:
            st.caption("No documents uploaded yet.")

        st.divider()

        # Quiz Generator
        st.markdown('<div class="sidebar-section">🧠 Quiz Generator</div>', unsafe_allow_html=True)
        quiz_topic = st.text_input("Topic", placeholder="e.g. TCP/IP, OSI Model...",
                                   label_visibility="collapsed", key="quiz_topic_input")
        num_q = st.slider("Questions", 3, 10, 5)
        if st.button("⚡ Generate Quiz", use_container_width=True, type="primary"):
            if not quiz_topic.strip():
                st.warning("Enter a topic first.")
            else:
                with st.spinner("Generating quiz..."):
                    try:
                        st.session_state.quiz_data     = api_quiz(quiz_topic.strip(), num_q)
                        st.session_state.quiz_answers  = {}
                        st.session_state.quiz_revealed = {}
                        st.session_state.quiz_submitted= False
                        st.success(f"✅ {len(st.session_state.quiz_data['questions'])} questions ready!")
                    except Exception as e:
                        st.error(str(e))

        st.divider()

        # Upcoming exams in sidebar
        exams = api_get_exams()
        upcoming = sorted(
            [e for e in exams if (date.fromisoformat(e["exam_date"]) - date.today()).days >= 0],
            key=lambda x: x["exam_date"]
        )[:3]
        if upcoming:
            st.markdown('<div class="sidebar-section">📅 Upcoming Exams</div>', unsafe_allow_html=True)
            for ex in upcoming:
                days_left = (date.fromisoformat(ex["exam_date"]) - date.today()).days
                color = "#f44336" if days_left <= 3 else "#FFC107"
                st.markdown(f"""
                <div style='font-size:0.8em;margin:4px 0;padding:6px 10px;
                            border-left:3px solid {color};border-radius:0 6px 6px 0;
                            background:rgba(255,255,255,0.03);'>
                    📌 <b>{ex['topic']}</b><br/>
                    <span style='color:{color};'>{days_left}d left</span> · {ex['exam_date']}
                </div>""", unsafe_allow_html=True)
            st.divider()

        # Chat options
        st.markdown('<div class="sidebar-section">⚙️ Options</div>', unsafe_allow_html=True)
        st.session_state.show_sources = st.toggle("Show source chunks",
                                                   value=st.session_state.show_sources)
        ca, cb = st.columns(2)
        with ca:
            if st.button("🗑️ Clear", use_container_width=True):
                api_clear_session(st.session_state.session_id)
                st.session_state.chat_history  = []
                st.session_state.session_id    = str(uuid.uuid4())
                st.session_state.quiz_data     = None
                st.session_state.quiz_answers  = {}
                st.session_state.quiz_revealed = {}
                st.session_state.quiz_submitted= False
                st.rerun()
        with cb:
            if st.button("🚪 Logout", use_container_width=True):
                for k in _defaults:
                    st.session_state[k] = _defaults[k]
                st.rerun()

        st.caption(f"Session: `{st.session_state.session_id[:8]}...`")

    # ── Main tabs ────────────────────────────
    st.title("🧑‍🎓 Student Portal")
    tab_chat, tab_pdfs, tab_quiz, tab_progress, tab_exams, tab_doubts = st.tabs([
        "💬 Ask AI Tutor", "📄 View Syllabus", "📝 Quiz",
        "📊 My Progress", "📅 Exam Schedule", "❓ Ask Admin"
    ])

    # ── Chat ─────────────────────────────────
    with tab_chat:
        st.subheader("Ask Your AI Tutor")
        st.caption("Answers are grounded strictly in uploaded syllabus content.")

        if not pdf_list:
            st.warning("No syllabus uploaded yet.", icon="📄")

        for msg in st.session_state.chat_history:
            if msg["role"] == "user":
                st.markdown(f'<div class="user-bubble">🧑‍🎓 {msg["content"]}</div>',
                            unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="assistant-bubble">🤖 {msg["content"]}</div>',
                            unsafe_allow_html=True)
                # TTS button under each AI answer
                tts_button(msg["content"], key=f"tts_{id(msg)}")
                if st.session_state.show_sources and msg.get("sources"):
                    with st.expander("📖 Sources", expanded=False):
                        for i, src in enumerate(msg["sources"], 1):
                            st.markdown(f'<div class="source-box"><b>Source {i}:</b> {src}</div>',
                                        unsafe_allow_html=True)

        st.divider()
        with st.form("chat_form", clear_on_submit=True):
            c1, c2 = st.columns([5, 1])
            with c1:
                user_input = st.text_input("q", label_visibility="collapsed",
                                           placeholder="Ask anything from your syllabus...")
            with c2:
                send = st.form_submit_button("Send ➤", use_container_width=True, type="primary")

        if send and user_input.strip():
            st.session_state.chat_history.append(
                {"role": "user", "content": user_input.strip(), "sources": []})
            with st.spinner("Thinking..."):
                try:
                    result = api_ask(user_input.strip(), st.session_state.session_id)
                    st.session_state.chat_history.append({
                        "role": "assistant",
                        "content": result["answer"],
                        "sources": result.get("sources", []),
                    })
                except Exception as e:
                    st.session_state.chat_history.append(
                        {"role": "assistant", "content": f"⚠️ Error: {e}", "sources": []})
            st.rerun()

    # ── PDF Viewer ───────────────────────────
    with tab_pdfs:
        st.subheader("📄 Course Materials")
        if not pdf_list:
            st.info("No documents available yet.", icon="📚")
        else:
            sel = st.selectbox("Select document", pdf_list, format_func=lambda x: f"📄 {x}")
            if sel:
                with st.spinner("Loading..."):
                    b64 = pdf_to_base64(sel)
                if b64:
                    st.markdown(
                        f'<iframe src="data:application/pdf;base64,{b64}" width="100%" height="800px" '
                        f'style="border:1px solid #e0e0e0;border-radius:8px;"></iframe>',
                        unsafe_allow_html=True)
                else:
                    st.error("Could not load PDF.")

    # ── Quiz ─────────────────────────────────
    with tab_quiz:
        st.subheader("📝 Practice Quiz")

        if st.session_state.quiz_data is None:
            st.info("👈 Enter a topic in the sidebar and click '⚡ Generate Quiz'.", icon="🎯")
        else:
            quiz = st.session_state.quiz_data
            questions = quiz["questions"]
            st.markdown(f"**Topic:** {quiz['topic']}  ·  **{len(questions)} questions**")
            st.divider()

            # Render each question
            for i, q in enumerate(questions):
                st.markdown(f"**Q{i+1}. {q['question']}**")
                options = q["options"] if isinstance(q, dict) else q.options
                answer  = q["answer"]  if isinstance(q, dict) else q.answer

                selected = st.radio(f"q_{i}", options=options,
                                    key=f"quiz_q_{i}", label_visibility="collapsed")
                st.session_state.quiz_answers[i] = selected

                if st.button("Reveal Answer", key=f"reveal_{i}"):
                    st.session_state.quiz_revealed[i] = True

                if st.session_state.quiz_revealed.get(i):
                    if selected == answer:
                        st.success(f"✅ Correct! → **{answer}**")
                    else:
                        st.error(f"❌ Wrong. Correct: **{answer}**")
                st.markdown("---")

            # Submit score
            if not st.session_state.quiz_submitted:
                if st.button("📊 Submit & Save Score", type="primary"):
                    correct = sum(
                        1 for i, q in enumerate(questions)
                        if st.session_state.quiz_answers.get(i) == (
                            q["answer"] if isinstance(q, dict) else q.answer)
                    )
                    total = len(questions)
                    api_save_score(st.session_state.username, quiz["topic"],
                                   correct, total, st.session_state.session_id)
                    st.session_state.quiz_submitted = True
                    st.success(f"Score saved! You got **{correct}/{total}** ({round(correct/total*100,1)}%)")
            else:
                correct = sum(
                    1 for i, q in enumerate(questions)
                    if st.session_state.quiz_answers.get(i) == (
                        q["answer"] if isinstance(q, dict) else q.answer)
                )
                st.info(f"Score already saved: **{correct}/{len(questions)}**", icon="✅")

            if st.button("🔄 New Quiz", type="secondary"):
                st.session_state.quiz_data      = None
                st.session_state.quiz_answers   = {}
                st.session_state.quiz_revealed  = {}
                st.session_state.quiz_submitted = False
                st.rerun()

    # ── My Progress ──────────────────────────
    with tab_progress:
        st.subheader("📊 My Quiz Progress")
        scores = api_get_scores(st.session_state.username)

        if not scores:
            st.info("No quiz scores yet. Complete a quiz and submit your score!", icon="📈")
        else:
            total   = len(scores)
            avg     = round(sum(s["score_pct"] for s in scores) / total, 1)
            best    = max(scores, key=lambda x: x["score_pct"])
            worst   = min(scores, key=lambda x: x["score_pct"])

            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Quizzes Taken", total)
            c2.metric("Avg Score", f"{avg}%")
            c3.metric("Best", f"{best['score_pct']}%", best["topic"])
            c4.metric("Needs Work", f"{worst['score_pct']}%", worst["topic"])

            st.divider()

            # Per-topic bar chart
            import pandas as pd
            df = pd.DataFrame(scores)
            df["attempt"] = df["topic"] + " #" + (df.groupby("topic").cumcount() + 1).astype(str)

            st.markdown("**Score per attempt**")
            st.bar_chart(df.set_index("attempt")["score_pct"])

            # Per-topic average
            st.markdown("**Average per topic**")
            topic_avg = df.groupby("topic")["score_pct"].mean().round(1).reset_index()
            topic_avg.columns = ["Topic", "Avg Score %"]
            st.dataframe(topic_avg, use_container_width=True, hide_index=True)

            with st.expander("📋 Full History"):
                st.dataframe(df[["topic", "correct", "total", "score_pct", "timestamp"]],
                             use_container_width=True, hide_index=True)

    # ── Exam Schedule ─────────────────────────
    with tab_exams:
        st.subheader("📅 Upcoming Exam Schedule")
        exams = api_get_exams()

        if not exams:
            st.info("No exams scheduled yet. Your admin will add them soon.", icon="📅")
        else:
            today = date.today()
            for ex in sorted(exams, key=lambda x: x["exam_date"]):
                try:
                    exam_dt   = date.fromisoformat(ex["exam_date"])
                    days_left = (exam_dt - today).days
                except Exception:
                    days_left = None

                is_today  = days_left == 0
                is_urgent = days_left is not None and 0 < days_left <= 3
                is_past   = days_left is not None and days_left < 0

                if is_past:
                    style = "border:1px solid #444;border-radius:12px;padding:14px;margin:8px 0;opacity:0.5;"
                    badge = "⬛ Past"
                elif is_today:
                    style = "border:2px solid #f44336;border-radius:12px;padding:14px;margin:8px 0;background:rgba(244,67,54,0.08);"
                    badge = "🔴 TODAY"
                elif is_urgent:
                    style = "border:1px solid #FF9800;border-radius:12px;padding:14px;margin:8px 0;background:rgba(255,152,0,0.08);"
                    badge = f"🟠 {days_left} days left"
                else:
                    style = "border:1px solid rgba(255,255,255,0.12);border-radius:12px;padding:14px;margin:8px 0;"
                    badge = f"🟢 {days_left} days left" if days_left is not None else ""

                st.markdown(f"""
                <div style='{style}'>
                    <div style='display:flex;justify-content:space-between;align-items:center;'>
                        <span style='font-size:1.05em;font-weight:600;'>📌 {ex['topic']}</span>
                        <span style='font-size:0.85em;'>{badge}</span>
                    </div>
                    <div style='color:#999;font-size:0.85em;margin-top:6px;'>
                        📄 {ex['pdf_filename']} &nbsp;·&nbsp; 📅 {ex['exam_date']} &nbsp;·&nbsp; ❓ {ex['num_questions']} questions
                    </div>
                </div>""", unsafe_allow_html=True)

                # If exam is today, offer to start it
                if is_today:
                    if st.button(f"🚀 Start Exam — {ex['topic']}", key=f"start_exam_{ex['id']}", type="primary"):
                        with st.spinner("Generating exam questions..."):
                            try:
                                data = api_quiz(ex["topic"], ex["num_questions"])
                                st.session_state.quiz_data      = data
                                st.session_state.quiz_answers   = {}
                                st.session_state.quiz_revealed  = {}
                                st.session_state.quiz_submitted = False
                                st.success("Exam ready! Switch to the 📝 Quiz tab.")
                            except Exception as e:
                                st.error(str(e))

    # ── Ask Admin (Doubts) ────────────────────
    with tab_doubts:
        st.subheader("❓ Ask Admin a Question")
        st.caption("Submit doubts or request new topics. Admin will reply here.")

        with st.form("doubt_form"):
            doubt_topic = st.text_input("Topic / Subject",
                                        placeholder="e.g. I need more content on Routing Protocols")
            doubt_msg   = st.text_area("Your Message", height=100,
                                       placeholder="Describe your doubt or what topics you'd like covered...")
            submit_doubt = st.form_submit_button("📨 Submit", type="primary")

        if submit_doubt:
            if not doubt_msg.strip():
                st.warning("Please write your message first.")
            else:
                try:
                    api_submit_doubt(st.session_state.username,
                                     doubt_msg.strip(),
                                     doubt_topic.strip() or "General")
                    st.success("✅ Your message has been sent to the admin!")
                    st.rerun()
                except Exception as e:
                    st.error(str(e))

        st.divider()
        st.subheader("📬 My Previous Doubts")
        my_doubts = api_get_my_doubts(st.session_state.username)

        if not my_doubts:
            st.info("You haven't submitted any doubts yet.", icon="💬")
        else:
            for d in sorted(my_doubts, key=lambda x: x["id"], reverse=True):
                replied = bool(d.get("reply"))
                st.markdown(f"""
                <div class="doubt-card">
                    <div style='display:flex;justify-content:space-between;'>
                        <b>#{d['id']} — {d['topic']}</b>
                        <span style='font-size:0.75em;color:#888;'>{d['timestamp'][:16].replace('T',' ')}</span>
                    </div>
                    <p style='margin:8px 0 4px 0;'>💬 {d['message']}</p>
                    {f'<div class="doubt-reply">🧑‍💼 <b>Admin replied:</b> {d["reply"]}<br/><span style="color:#888;font-size:0.75em;">{(d.get("replied_at") or "")[:16].replace("T"," ")}</span></div>'
                     if replied else
                     '<span style="color:#888;font-size:0.8em;">⏳ Awaiting admin reply...</span>'}
                </div>""", unsafe_allow_html=True)
                st.divider()

# ─────────────────────────────────────────────
# ROUTER
# ─────────────────────────────────────────────
if not st.session_state.logged_in:
    show_login()
elif st.session_state.role == "admin":
    show_admin()
else:
    show_student()
