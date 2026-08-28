import streamlit as st
from database.sql_models import Resume
from database.sql_db import SessionLocal
from core.prompt_engine import extract_resume_sections

# Import Modular Step Components
from components.candidate.step1_cv_builder import render_step1
from components.candidate.step2_jd_swot import render_step2
from components.candidate.step3_ats_tailor import render_step3
from components.candidate.step4_multi_jd import render_step4
from components.candidate.step5_skill_matrix import render_step5
from components.candidate.step6_mock_drive import render_step6

# ==============================================================================
# Page Configuration & Guardrails
# ==============================================================================
st.set_page_config(page_title="Candidate Launchpad", layout="wide", page_icon="🎓")

if "auth_user" not in st.session_state or not st.session_state.auth_user:
    st.warning("Please sign in from the main portal to access your Candidate Workspace.")
    st.stop()

current_user = st.session_state.auth_user
user_role = current_user.get("role", "candidate")

if user_role not in ["candidate", "admin"]:
    st.error(f"Access restricted to Candidates. Your current active role is: '{user_role.upper()}'.")
    st.stop()

# Initialize Global Persistent Session State Variables
if "cand_cv" not in st.session_state:
    st.session_state.cand_cv = ""
if "cand_jd" not in st.session_state:
    st.session_state.cand_jd = ""
if "master_rev" not in st.session_state:
    st.session_state.master_rev = 0
if "sec_polish_rev" not in st.session_state:
    st.session_state.sec_polish_rev = {}
if "sec_current" not in st.session_state:
    st.session_state.sec_current = {}
if "sec_ai" not in st.session_state:
    st.session_state.sec_ai = {}
if "sec_mod" not in st.session_state:
    st.session_state.sec_mod = {}
if "swot_result" not in st.session_state:
    st.session_state.swot_result = None

st.title("🎓 Candidate Career Acceleration Launchpad")
st.caption(f"Authenticated as: **{current_user.get('full_name') or current_user.get('email')}** ({current_user.get('email')})")

# ==============================================================================
# Pre-load Existing Candidate Resume if available
# ==============================================================================
session = SessionLocal()
try:
    if not st.session_state.cand_cv:
        existing_res = session.query(Resume).filter(
            Resume.user_id == current_user.get("id")
        ).order_by(Resume.created_at.desc()).first()
        if existing_res:
            loaded_text = existing_res.markdown_content or existing_res.raw_content or ""
            st.session_state.cand_cv = loaded_text
finally:
    session.close()

# Synchronize sections on first load
if st.session_state.cand_cv:
    extracted = extract_resume_sections(st.session_state.cand_cv)
    for k, v in extracted.items():
        if k not in st.session_state.sec_current or not st.session_state.sec_current[k]:
            st.session_state.sec_current[k] = v
        if k not in st.session_state.sec_mod or not st.session_state.sec_mod[k]:
            st.session_state.sec_mod[k] = v
        if k not in st.session_state.sec_polish_rev:
            st.session_state.sec_polish_rev[k] = 0

# ==============================================================================
# Modular Step Tabs Router (Steps 1 through 6)
# ==============================================================================
t1, t2, t3, t4, t5, t6 = st.tabs([
    "📝 Step 1: CV Builder & 3-Box Copilot",
    "🎯 Step 2: JD Match, Section Fit & SWOT",
    "⚡ Step 3: ATS Auto-Tailor & Residual Gaps",
    "🏆 Step 4: Multi-JD Match & Cover Letters",
    "🗺️ Step 5: Market Skill Matrix & 8-Week Plan",
    "🎙️ Step 6: Multi-Track Mock Drive & Prep"
])

with t1:
    render_step1(current_user)

with t2:
    render_step2()

with t3:
    render_step3(current_user)

with t4:
    render_step4()

with t5:
    render_step5()

with t6:
    render_step6()
