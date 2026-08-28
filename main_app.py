import streamlit as st
from config.settings import settings
from database.sql_db import sql_db
from database.sql_models import User

# Configure application-wide layout and title
st.set_page_config(
    page_title="PragyanAI Enterprise Talent Suite",
    layout="wide",
    page_icon="🚀",
    initial_sidebar_state="expanded"
)

# Initialize session state authentication token
if "auth_user" not in st.session_state:
    st.session_state.auth_user = None


def render_auth_gateway():
    """Renders the secure Login and Registration tabs for Candidates, Employers, and Admins."""
    st.markdown("<h1 style='text-align: center; color: #1A365D;'>🚀 PragyanAI Talent Intelligence Suite</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #4A5568;'>Autonomous Multi-Tenant Recruitment, RAG Intelligence, and Candidate Upskilling Engine</p>", unsafe_allow_html=True)
    st.markdown("---")

    col_center = st.columns([1, 2, 1])[1]

    with col_center:
        tab_login, tab_register = st.tabs(["🔑 Sign In", "📝 Create Account"])

        # ----------------- TAB 1: USER SIGN IN -----------------
        with tab_login:
            st.subheader("Secure Platform Sign In")
            with st.form("signin_form", clear_on_submit=False):
                login_email = st.text_input("Work / Academic Email", placeholder="user@domain.com")
                login_password = st.text_input("Password", type="password", placeholder="••••••••")
                submit_login = st.form_submit_button("Sign In to Workspace", use_container_width=True, type="primary")

                if submit_login:
                    if not login_email.strip() or not login_password.strip():
                        st.warning("Please provide both email and password.")
                    else:
                        user_record = sql_db.authenticate_user(login_email, login_password)
                        if not user_record:
                            st.error("Invalid credentials. Please verify your email and password.")
                        elif not user_record.get("is_approved", False):
                            st.warning("Your account is pending administrator verification. Please check back shortly.")
                        else:
                            st.session_state.auth_user = user_record
                            st.success(f"Welcome back, {user_record.get('full_name') or user_record.get('email')}!")
                            st.rerun()

            with st.expander("Default Test Credentials (from database seed)"):
                st.markdown("""
                - **Admin:** `admin@pragyan.ai` | `admin123`
                - **Candidate:** `candidate@pragyan.ai` | `candidate123`
                - **Hiring Company:** `recruiter@enterprise.com` | `company123`
                """)

        # ----------------- TAB 2: USER REGISTRATION -----------------
        with tab_register:
            st.subheader("New Account Registration")
            with st.form("signup_form", clear_on_submit=True):
                reg_name = st.text_input("Full Name / Organization Name", placeholder="e.g., Jane Doe / Apex AI Labs")
                reg_email = st.text_input("Email Address", placeholder="e.g., jane@example.com")
                reg_pass = st.text_input("Set Secure Password", type="password", placeholder="••••••••")
                reg_role = st.selectbox(
                    "Select Account Identity:",
                    ["candidate", "company"],
                    format_func=lambda x: "🎓 Candidate / Student Job Seeker" if x == "candidate" else "🏢 Hiring Company / Recruiter"
                )

                submit_register = st.form_submit_button("Create Account", use_container_width=True, type="primary")

                if submit_register:
                    if not reg_email.strip() or not reg_pass.strip() or not reg_name.strip():
                        st.warning("All fields are required for registration.")
                    elif len(reg_pass) < 6:
                        st.warning("Password must be at least 6 characters.")
                    else:
                        reg_result = sql_db.register_user(
                            email=reg_email,
                            password=reg_pass,
                            role=reg_role,
                            full_name=reg_name
                        )
                        if reg_result["success"]:
                            if reg_role == "candidate":
                                st.success("Candidate account created successfully! You may now sign in.")
                            else:
                                st.info("Company account registered! Your account has been submitted to the Admin queue for moderation.")
                        else:
                            st.error(reg_result["message"])


def render_authenticated_home():
    """Renders the dashboard gateway and quick actions once a user is authenticated."""
    user = st.session_state.auth_user
    role = user.get("role", "candidate")
    user_name = user.get("full_name") or user.get("email")

    # Sidebar Navigation & User Info
    st.sidebar.markdown(f"### Logged In")
    st.sidebar.markdown(f"**User:** `{user.get('email')}`")
    st.sidebar.markdown(f"**Role:** `{role.upper()}`")
    st.sidebar.markdown("---")

    if st.sidebar.button("🚪 Sign Out", use_container_width=True):
        st.session_state.auth_user = None
        st.rerun()

    # Main Workspace Welcome Hub
    st.markdown(f"## Welcome to your Workspace, {user_name}!")
    st.markdown(f"**Authenticated Role:** `{role.upper()}`")
    st.markdown("---")

    # Role-Specific Routing Cards
    if role == "admin":
        st.success("👑 **Admin Platform Governance Active**")
        st.markdown("""
        You have global governance privileges. Use the left sidebar to navigate to:
        - **`1_👑_Admin_Dashboard`**: Access conversion funnels, moderate pending employer accounts, and ingest global JDs/resumes into SQL and ChromaDB vector stores.
        - **`4_💬_RAG_Talent_Chat`**: Conduct multi-context RAG queries across the entire candidate pool.
        """)

        col1, col2, col3 = st.columns(3)
        with col1:
            st.info("📊 **Platform Telemetry**\n\nMonitor live candidate applications, JD distributions, and conversion rates.")
        with col2:
            st.warning("🛡️ **Tenant Approvals**\n\nReview, approve, or reject pending employer registration requests.")
        with col3:
            st.success("📥 **Universal Ingest**\n\nVectorize bulk resumes, LinkedIn URLs, and PDF job descriptions.")

    elif role == "candidate":
        st.info("🎓 **Candidate Career Launchpad Active**")
        st.markdown("""
        Use the left sidebar navigation to launch your career preparation tools:
        - **`2_🎓_Candidate_Dashboard`**: Access all 6 career launchpad tools:
            1. **Resume Builder & Studio**: Convert raw notes to ATS-friendly Markdown & export ReportLab PDFs.
            2. **JD Match & SWOT**: Run deep gap analysis against any target job description.
            3. **ATS Keyword Optimizer**: Organic keyword alignment for higher screening scores.
            4. **Smart Cover Letter**: Synthesize targeted, high-converting cover letters.
            5. **Voice & Text Mock Room**: Interactive AI mock interviews with gTTS speech and Whisper transcription.
            6. **Upskill Roadmap**: Personalized 4-week project plans with DDGS search and YouTube video tutorials.
        - **`4_💬_RAG_Talent_Chat`**: Grounded conversational chat with your CV and target JDs.
        """)

    elif role == "company":
        st.info("🏢 **Hiring Company Command Center Active**")
        st.markdown("""
        Manage your end-to-end talent pipeline using the sidebar navigation:
        - **`3_🏢_Hiring_Company_Dashboard`**: Access the employer recruitment engine:
            1. **Job Position Studio**: Publish roles and unpack bulk ZIP/PDF candidate vaults.
            2. **Candidate Pre-Screening**: Validate notice periods, compensation, and relocation feasibility.
            3. **Top-K Ranking & SWOT**: Semantic vector matching with SWOT diagnostics.
            4. **SQL Interview Scheduler**: Schedule interview rounds and generate virtual meeting links.
            5. **Pipeline CSV Export**: Export structured candidate evaluation reports.
        - **`4_💬_RAG_Talent_Chat`**: Query the candidate digital CV bank with grounded RAG.
        """)

    st.markdown("---")
    st.caption("PragyanAI Enterprise Talent Platform — Multi-Tenant Agentic Architecture (Groq + LangChain + SQLAlchemy + ChromaDB)")


# ----------------- MAIN RUNNER -----------------
if not st.session_state.auth_user:
    render_auth_gateway()
else:
    render_authenticated_home()
