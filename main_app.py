import streamlit as st
import hashlib
from config.settings import settings
from database.sql_models import Base, User, JobDescription, Resume, Application
from database.sql_db import sql_db, SessionLocal, engine

# ==============================================================================
# Application Configuration
# ==============================================================================
st.set_page_config(
    page_title="PragyanAI Enterprise Talent Suite",
    layout="wide",
    page_icon="🚀",
    initial_sidebar_state="expanded"
)

# ==============================================================================
# Self-Healing Database Bootstrap (Ensures tables & credentials always exist)
# ==============================================================================
def ensure_database_initialized():
    """Initializes tables and inserts seed credentials if the database is empty or missing."""
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    try:
        user_count = session.query(User).count()
        if user_count == 0:
            default_accounts = [
                ("admin@pragyan.ai", "admin123", "admin", "System Administrator", True),
                ("candidate@pragyan.ai", "candidate123", "candidate", "Aarav Sharma", True),
                ("recruiter@enterprise.com", "company123", "company", "Apex AI Labs HR", True),
                ("pending_recruiter@startup.io", "company123", "company", "NextGen Startup", False),
            ]
            for email, pwd, role, name, approved in default_accounts:
                pwd_hash = hashlib.sha256(pwd.encode("utf-8")).hexdigest()
                new_user = User(
                    email=email.strip().lower(),
                    password_hash=pwd_hash,
                    role=role,
                    full_name=name,
                    is_approved=approved
                )
                session.add(new_user)
            session.commit()
    except Exception as e:
        session.rollback()
    finally:
        session.close()

# Run database verification hook on application load
ensure_database_initialized()

# ==============================================================================
# Session State Initialization
# ==============================================================================
if "auth_user" not in st.session_state:
    st.session_state.auth_user = None


# ==============================================================================
# Authentication Gateway (Login & Registration)
# ==============================================================================
def render_auth_gateway():
    """Renders the secure Multi-Tenant Login & Registration portal."""
    st.markdown(
        "<h1 style='text-align: center; color: #1A365D;'>🚀 PragyanAI Talent Intelligence Suite</h1>",
        unsafe_allow_html=True
    )
    st.markdown(
        "<p style='text-align: center; color: #4A5568;'>Autonomous Multi-Tenant Recruitment, RAG Intelligence, and Candidate Upskilling Engine</p>",
        unsafe_allow_html=True
    )
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
                    cleaned_email = login_email.strip().lower()
                    cleaned_password = login_password.strip()

                    if not cleaned_email or not cleaned_password:
                        st.warning("Please provide both email and password.")
                    else:
                        user_record = sql_db.authenticate_user(cleaned_email, cleaned_password)
                        if not user_record:
                            st.error("Invalid credentials. Please verify your email and password.")
                        elif not user_record.get("is_approved", False):
                            st.warning("Your account is pending administrator verification. Please check back shortly.")
                        else:
                            st.session_state.auth_user = user_record
                            st.success(f"Welcome back, {user_record.get('full_name') or user_record.get('email')}!")
                            st.rerun()

            with st.expander("Default Test Credentials (Pre-Seeded)", expanded=True):
                st.markdown("""
                - **Admin Console:** `admin@pragyan.ai` | `admin123`
                - **Candidate / Student:** `candidate@pragyan.ai` | `candidate123`
                - **Hiring Company / Employer:** `recruiter@enterprise.com` | `company123`
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
                    cleaned_reg_email = reg_email.strip().lower()
                    cleaned_reg_pass = reg_pass.strip()
                    cleaned_reg_name = reg_name.strip()

                    if not cleaned_reg_email or not cleaned_reg_pass or not cleaned_reg_name:
                        st.warning("All fields are required for registration.")
                    elif len(cleaned_reg_pass) < 6:
                        st.warning("Password must be at least 6 characters.")
                    else:
                        reg_result = sql_db.register_user(
                            email=cleaned_reg_email,
                            password=cleaned_reg_pass,
                            role=reg_role,
                            full_name=cleaned_reg_name
                        )
                        if reg_result["success"]:
                            if reg_role == "candidate":
                                st.success("Candidate account created successfully! You can now sign in using the 'Sign In' tab.")
                            else:
                                st.info("Company account registered! Your account has been submitted to the Admin queue for moderation.")
                        else:
                            st.error(reg_result["message"])


# ==============================================================================
# Authenticated User Hub & Routing Gateway
# ==============================================================================
def render_authenticated_home():
    """Renders the dashboard gateway and navigation routing after login."""
    user = st.session_state.auth_user
    role = user.get("role", "candidate")
    user_name = user.get("full_name") or user.get("email")

    # Sidebar Profile & Logout
    st.sidebar.markdown("### Active Session")
    st.sidebar.markdown(f"**User:** `{user.get('email')}`")
    st.sidebar.markdown(f"**Role:** `{role.upper()}`")
    st.sidebar.markdown("---")

    if st.sidebar.button("🚪 Sign Out", use_container_width=True):
        st.session_state.auth_user = None
        st.rerun()

    # Workspace Header
    st.markdown(f"## Welcome to your Workspace, {user_name}!")
    st.markdown(f"**Authenticated Role Identity:** `{role.upper()}`")
    st.markdown("---")

    # Role-Specific Dashboard Directions
    if role == "admin":
        st.success("👑 **Admin Platform Governance Active**")
        st.markdown("""
        You have global system privileges. Access your dedicated management pages from the left sidebar:
        - **`1_👑_Admin_Dashboard`**: Platform telemetry, conversion funnels, tenant moderation queue, and universal catalog ingestion.
        - **`4_💬_RAG_Talent_Chat`**: Multi-context RAG intelligence across resumes and job descriptions.
        """)

        c1, c2, c3 = st.columns(3)
        with c1:
            st.info("📊 **Platform Telemetry**\n\nMonitor live conversion funnels, user distributions, and total platform metrics.")
        with c2:
            st.warning("🛡️ **Tenant Approvals**\n\nReview, authorize, or delete pending employer registration applications.")
        with c3:
            st.success("📥 **Universal Ingestion**\n\nDirectly ingest and vectorize bulk resumes, URLs, and PDF job descriptions.")

    elif role == "candidate":
        st.info("🎓 **Candidate Career Launchpad Active**")
        st.markdown("""
        Use the left sidebar navigation to launch your career preparation tools:
        - **`2_🎓_Candidate_Dashboard`**: Access the 6-step candidate preparation workflow:
            1. **Resume Builder & Studio**: Convert raw notes to ATS Markdown & export publication-grade PDFs.
            2. **JD Match & SWOT**: Run comprehensive gap analysis and SWOT matrix generation against any job description.
            3. **ATS Keyword Optimizer**: Organic keyword alignment to maximize screening pass rates.
            4. **Smart Cover Letter**: Synthesize targeted, high-converting cover letters.
            5. **Voice & Text Mock Room**: Interactive AI mock interviews with speech playback and Whisper transcription.
            6. **Upskill Roadmap**: Tailored 4-week project roadmaps with free web guides and YouTube crash courses.
        - **`4_💬_RAG_Talent_Chat`**: Grounded conversational assistant to query resumes, JDs, and interview preparation topics.
        """)

    elif role == "company":
        st.info("🏢 **Hiring Company Command Center Active**")
        st.markdown("""
        Manage your talent pipeline from candidate intake to final interview dispatch:
        - **`3_🏢_Hiring_Company_Dashboard`**: Access the employer recruitment engine:
            1. **Job Position Studio**: Publish positions and upload bulk ZIP or PDF candidate vaults.
            2. **Candidate Pre-Screening**: Screen compensation, notice period buyout, and relocation fit.
            3. **Top-K Ranking & SWOT**: Semantic vector matching with SWOT diagnostics for every candidate.
            4. **SQL Interview Scheduler**: Schedule interview rounds and generate meeting rooms.
            5. **Pipeline CSV Export**: Export comprehensive evaluation shortlists.
        - **`4_💬_RAG_Talent_Chat`**: Interactive RAG chat to inspect candidate qualifications and generate targeted interview questions.
        """)

    st.markdown("---")
    st.caption("PragyanAI Enterprise Talent Platform — Multi-Tenant Agentic Architecture (Groq + LangChain + SQLAlchemy + ChromaDB)")


# ==============================================================================
# Main Entrypoint
# ==============================================================================
if not st.session_state.auth_user:
    render_auth_gateway()
else:
    render_authenticated_home()
