import streamlit as st
import os
import base64
import subprocess
import requests
import time

# ---------------- CONFIG ----------------

st.set_page_config(
    page_title="AI Tutor Admin",
    page_icon="📚",
    layout="wide"
)

UPLOAD_FOLDER = "pdfs"
BACKEND_URL = "http://localhost:8000"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ---------------- CSS ----------------

st.markdown("""
<style>

.stApp {
    background:
        radial-gradient(circle at top left, rgba(124,58,237,0.35), transparent 35%),
        radial-gradient(circle at bottom right, rgba(192,38,211,0.25), transparent 35%),
        linear-gradient(135deg, #070014, #13002e, #260052);
    color: white;
}

header[data-testid="stHeader"] {
    display: none;
}

#MainMenu {
    visibility: hidden;
}

footer {
    visibility: hidden;
}

.block-container {
    padding-top: 2rem;
    max-width: 1250px;
}

h1, h2, h3, h4, p, label {
    color: white !important;
}

[data-testid="stSidebar"] {
    background: rgba(10, 0, 25, 0.95);
}

.platform-card,
.feature-card,
.big-card,
.login-panel,
.admin-card,
.pdf-card {
    background: rgba(255,255,255,0.08);
    border: 1px solid rgba(255,255,255,0.12);
    border-radius: 22px;
    backdrop-filter: blur(18px);
    box-shadow: 0 20px 50px rgba(0,0,0,0.25);
}

.platform-card {
    padding: 28px;
    margin-bottom: 25px;
}

.hero-title {
    font-size: 42px;
    font-weight: 800;
    margin-bottom: 8px;
}

.hero-sub {
    color: #d8b4fe;
    font-size: 17px;
}

.feature-card {
    padding: 20px;
    margin-bottom: 16px;
    font-size: 18px;
    font-weight: 600;
}

.big-card {
    padding: 28px;
    margin-top: 30px;
}

.login-panel {
    padding: 35px;
    margin-top: 25px;
    margin-bottom: 25px;
    text-align: center;
}

.demo-box {
    background: rgba(255,255,255,0.07);
    border: 1px solid rgba(255,255,255,0.14);
    border-radius: 15px;
    padding: 14px;
    text-align: center;
    color: white;
}

.admin-card {
    padding: 25px;
    margin-top: 20px;
}

.pdf-card {
    padding: 18px;
    margin-bottom: 15px;
}

.stButton button {
    width: 100%;
    height: 52px;
    border-radius: 14px;
    border: none;
    background: linear-gradient(90deg, #9333ea, #c026d3);
    color: white;
    font-size: 17px;
    font-weight: 700;
}

.stButton button:hover {
    background: linear-gradient(90deg, #7e22ce, #a21caf);
    color: white;
}

[data-testid="stMetric"] {
    background: rgba(255,255,255,0.08);
    border: 1px solid rgba(255,255,255,0.12);
    padding: 18px;
    border-radius: 18px;
}

input {
    border-radius: 12px !important;
}

</style>
""", unsafe_allow_html=True)

# ---------------- BACKEND AUTO START ----------------

def is_backend_running():
    try:
        response = requests.get(
            BACKEND_URL,
            timeout=2
        )

        return response.status_code == 200

    except:
        return False


def start_backend():
    if not is_backend_running():

        try:
            subprocess.Popen(
                ["python", "../backend/main.py"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )

            time.sleep(2)

        except Exception as e:
            st.warning(
                f"Backend could not start automatically: {e}"
            )


# ---------------- PDF PREVIEW ----------------

def show_pdf(file_path):
    try:
        with open(file_path, "rb") as pdf_file:
            encoded_pdf = base64.b64encode(
                pdf_file.read()
            ).decode("utf-8")

        pdf_display = f"""
        <iframe
            src="data:application/pdf;base64,{encoded_pdf}"
            width="100%"
            height="650px"
            style="
                border:none;
                border-radius:16px;
                background:white;
            ">
        </iframe>
        """

        st.markdown(
            pdf_display,
            unsafe_allow_html=True
        )

    except Exception as e:
        st.error(
            f"Unable to preview PDF: {e}"
        )

        # ---------------- LOGIN PAGE ----------------

def show_login():

    left, right = st.columns([1.4, 1])

    # ---------------- LEFT SIDE ----------------

    with left:

        st.markdown("""
        <div class="platform-card">
            <div class="hero-title">
                🎓 AI Tutor Platform
          
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div class="feature-card">
            🤖 AI-Powered Learning
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div class="feature-card">
            📖 Smart Document Analysis
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div class="feature-card">
            🎯 Auto Quiz Generation
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div class="feature-card">
            🔒 Secure & Private
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div class="big-card">

        <h3>
        ✨ Personalized Learning Experience
        </h3>

        <p>
        Upload syllabus PDFs, chat with AI,
        generate quizzes, analyze academic
        documents and create customized
        learning experiences for students.
        </p>

        </div>
        """, unsafe_allow_html=True)

    # ---------------- RIGHT SIDE ----------------

    with right:

        st.markdown("""
        <div class="login-panel">

        <h1 style="
            text-align:center;
            color:white;
            margin-bottom:10px;
        ">
            Welcome Back
        </h1>

        <p style="
            text-align:center;
            color:#d1d5db;
        ">
            Sign in to continue
        </p>

        </div>
        """, unsafe_allow_html=True)

        username = st.text_input(
            "👤 Username",
            placeholder="Enter username"
        )

        password = st.text_input(
            "🔒 Password",
            type="password",
            placeholder="Enter password"
        )

        login = st.button(
            "🚀 Sign In",
            use_container_width=True
        )

        st.markdown("<br>", unsafe_allow_html=True)

        st.markdown("""
        <h4 style="
            text-align:center;
            color:#d1d5db;
        ">
            Demo Access
        </h4>
        """, unsafe_allow_html=True)

        c1, c2 = st.columns(2)

        with c1:

            st.markdown("""
            <div class="demo-box">
                <b>Admin</b><br>
                admin<br>
                admin
            </div>
            """, unsafe_allow_html=True)

        with c2:

            st.markdown("""
            <div class="demo-box">
                <b>Student</b><br>
                student<br>
                student
            </div>
            """, unsafe_allow_html=True)

        if login:

            if (
                username == "admin"
                and password == "admin"
            ):

                st.session_state.logged_in = True
                st.session_state.role = "admin"

                st.rerun()

            else:

                st.error(
                    "Invalid Credentials"
                )

                # ---------------- ADMIN DASHBOARD ----------------

def show_admin():

    pdf_files = [
        file for file in os.listdir(UPLOAD_FOLDER)
        if file.lower().endswith(".pdf")
    ]

    # ---------------- SIDEBAR ----------------

    with st.sidebar:

        st.title("📚 AI Tutor")

        st.markdown("---")

        st.write("🏠 Dashboard")
        st.write("📤 Upload PDFs")
        st.write("📁 Manage PDFs")

        st.markdown("---")

        if st.button("🚪 Logout"):

            st.session_state.logged_in = False
            st.session_state.role = None

            st.rerun()

    # ---------------- HEADER ----------------

    st.markdown("""
    <h1>
        Welcome Admin 👋
    </h1>

    <p style="
        color:#d8b4fe;
        font-size:18px;
    ">
        Manage your learning resources and PDFs
    </p>
    """, unsafe_allow_html=True)

    # ---------------- STATS ----------------

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.metric(
            "📄 PDFs",
            len(pdf_files)
        )

    with c2:
        st.metric(
            "📚 Subjects",
            "6"
        )

    with c3:
        st.metric(
            "💾 Storage",
            "120 MB"
        )

    with c4:
        st.metric(
            "🟢 Backend",
            "Online"
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # ---------------- TABS ----------------

    tab1, tab2 = st.tabs([
        "📤 Upload Documents",
        "📁 Manage Documents"
    ])

    # ==================================================
    # UPLOAD TAB
    # ==================================================

    with tab1:

        st.markdown("""
        <div class="admin-card">
        <h3>📤 Upload Course Material</h3>
        </div>
        """, unsafe_allow_html=True)

        uploaded_files = st.file_uploader(
            "Choose PDF Files",
            type=["pdf"],
            accept_multiple_files=True
        )

        if uploaded_files:

            for uploaded_file in uploaded_files:

                file_path = os.path.join(
                    UPLOAD_FOLDER,
                    uploaded_file.name
                )

                with open(
                    file_path,
                    "wb"
                ) as f:

                    f.write(
                        uploaded_file.getbuffer()
                    )

                st.success(
                    f"✅ {uploaded_file.name} uploaded successfully"
                )

    # ==================================================
    # MANAGE TAB
    # ==================================================

    with tab2:

        st.subheader("Uploaded PDFs")

        pdf_files = [
            file for file in os.listdir(UPLOAD_FOLDER)
            if file.lower().endswith(".pdf")
        ]

        if not pdf_files:

            st.info(
                "No PDF uploaded yet."
            )

        else:

            for pdf in pdf_files:

                file_path = os.path.join(
                    UPLOAD_FOLDER,
                    pdf
                )

                st.markdown(
                    '<div class="pdf-card">',
                    unsafe_allow_html=True
                )

                col1, col2, col3 = st.columns(
                    [4,1,1]
                )

                with col1:

                    st.write(
                        f"📄 **{pdf}**"
                    )

                with col2:

                    preview = st.button(
                        "Preview",
                        key=f"preview_{pdf}"
                    )

                with col3:

                    delete = st.button(
                        "Delete",
                        key=f"delete_{pdf}"
                    )

                if preview:

                    st.subheader(
                        f"Preview: {pdf}"
                    )

                    show_pdf(
                        file_path
                    )

                if delete:

                    os.remove(
                        file_path
                    )

                    st.success(
                        f"{pdf} deleted successfully"
                    )

                    st.rerun()

                st.markdown(
                    "</div>",
                    unsafe_allow_html=True
                )


# ---------------- MAIN APP ----------------

def main():

    if "backend_started" not in st.session_state:

        start_backend()

        st.session_state.backend_started = True

    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False

    if "role" not in st.session_state:
        st.session_state.role = None

    if st.session_state.logged_in:

        if st.session_state.role == "admin":

            show_admin()

        else:

            st.error(
                "Unauthorized role"
            )

    else:

        show_login()


if __name__ == "__main__":
    main()