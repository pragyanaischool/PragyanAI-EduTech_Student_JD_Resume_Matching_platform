import streamlit as st
import pandas as pd
from database.sql_models import JobDescription, Resume, Application
from database.sql_db import sql_db, SessionLocal
from database.chroma_db import chroma
from core.parsers import parse_pdf, parse_docx
from core.pdf_builder import generate_pdf_report
from core.prompt_engine import (
    generate_enterprise_job_description,
    match_cv_to_jd,
    screen_candidate_logistics,
)

# ==============================================================================
# Page Configuration & Guardrails
# ==============================================================================
st.set_page_config(page_title="Employer Talent Hub", layout="wide", page_icon="🏢")

if "auth_user" not in st.session_state or not st.session_state.auth_user:
    st.warning("Please sign in from the main portal to access the Employer Portal.")
    st.stop()

current_user = st.session_state.auth_user
raw_role = current_user.get("role", "")
user_role = str(raw_role).lower().strip()

# Allow company, recruiter, employer, hiring_manager, and admin roles
ALLOWED_EMPLOYER_ROLES = ["company", "recruiter", "employer", "hiring_manager", "admin"]

if user_role not in ALLOWED_EMPLOYER_ROLES:
    st.error(f"Access restricted to Recruiters & Hiring Managers. Your active role is: '{raw_role}'.")
    st.stop()

# Initialize Session State Variables
if "draft_jd_markdown" not in st.session_state:
    st.session_state.draft_jd_markdown = ""
if "jd_editor_rev" not in st.session_state:
    st.session_state.jd_editor_rev = 0

st.title("🏢 Hiring Manager & Recruiter Command Center")
st.caption(f"Authenticated as: **{current_user.get('full_name') or current_user.get('email')}** ({current_user.get('email')}) — Role: `{raw_role.upper()}`")

# Navigation Tabs
tab_publish, tab_inventory, tab_matcher = st.tabs([
    "➕ 1. Publish New Position (JD)",
    "🗄️ 2. Active Positions Inventory",
    "🎯 3. Candidate Matching & Pipeline"
])

# ==============================================================================
# TAB 1: PUBLISH NEW JOB POSITION (JD)
# ==============================================================================
with tab_publish:
    st.header("Publish New Job Position (JD)")
    st.caption("Configure position parameters, synthesize full enterprise specifications with AI or ingest existing documents, review, edit, and index.")

    # --------------------------------------------------------------------------
    # 1. Metadata Selection Form
    # --------------------------------------------------------------------------
    with st.expander("⚙️ Step 1: Position Metadata & Parameters", expanded=True):
        c_title, c_dept = st.columns(2)
        with c_title:
            pos_title = st.text_input(
                "Job Position Title *",
                value="Senior AI Systems Engineer",
                placeholder="e.g. Lead MLOps Architect, Full Stack Engineer..."
            )
        with c_dept:
            pos_dept = st.selectbox(
                "Department / Unit *",
                [
                    "Artificial Intelligence & ML",
                    "Core Software Engineering",
                    "Data Engineering & Analytics",
                    "Cloud, DevOps & Infrastructure",
                    "Cybersecurity & Systems",
                    "Product Management & Design",
                    "Embedded Systems & EDA"
                ]
            )

        c_loc, c_exp, c_comp = st.columns(3)
        with c_loc:
            pos_loc = st.selectbox(
                "Work Location Model *",
                ["Remote (Worldwide)", "Remote (India)", "Hybrid (Bengaluru)", "Hybrid (Hyderabad / Pune)", "On-site (Bengaluru)", "On-site (San Francisco)"]
            )
        with c_exp:
            pos_exp = st.selectbox(
                "Years of Experience Range *",
                ["0–1 Years (Graduate / Entry)", "1–3 Years (Junior)", "3–5 Years (Mid-Level)", "5–8 Years (Senior)", "8–12 Years (Lead / Staff)", "12+ Years (Principal / Director)"]
            )
        with c_comp:
            comp_type = st.selectbox(
                "Compensation Structure *",
                ["Competitive Market Band (₹18L – ₹35L / $120k – $180k)", "Fixed Annual CTC + Equity ESOPs", "Hourly / Retainer Contract", "Non-paid / Academic Internship", "Performance-Linked Incentive Base"]
            )

        c_tech, c_biz = st.columns(2)
        with c_tech:
            pos_tech = st.selectbox(
                "Primary Technology Domain *",
                [
                    "Generative AI, LLMs & Agentic Systems (LangGraph, Groq, vLLM)",
                    "High-Throughput Backend & Microservices (Python, FastAPI, Go)",
                    "Modern Web & Frontend Architectures (React, Next.js, TypeScript)",
                    "Distributed Vector Stores & DBMS (ChromaDB, PostgreSQL, Redis)",
                    "Cloud Native & Container Orchestration (Docker, Kubernetes, AWS/GCP)",
                    "Computer Vision & Edge AI (PyTorch, OpenCV, TensorRT)",
                    "EDA, PCB Verification & Embedded Firmware (C/C++, Linux Kernel)"
                ]
            )
        with c_biz:
            pos_biz = st.selectbox(
                "Business / Industry Domain *",
                [
                    "EdTech & Adaptive Learning Platforms",
                    "Enterprise SaaS & Venture Studios",
                    "FinTech, WealthTech & Banking Solutions",
                    "Healthcare & Biomedical Intelligence",
                    "E-Commerce, Supply Chain & Logistics",
                    "Electronic Design Automation (EDA) & Hardware Tech"
                ]
            )

    # --------------------------------------------------------------------------
    # 2. Ingestion Source & Generation Hub
    # --------------------------------------------------------------------------
    st.subheader("2. Ingestion Source & Content Synthesis")
    ingest_mode = st.radio(
        "Choose JD Ingestion Mode:",
        ["🤖 AI Autonomous Generation (Recommended)", "📄 Upload Existing Document (PDF / DOCX)", "📝 Direct Markdown / Text Paste"],
        horizontal=True
    )

    if ingest_mode == "🤖 AI Autonomous Generation (Recommended)":
        col_ai_notes, col_ai_btn = st.columns([3, 1])
        with col_ai_notes:
            extra_context = st.text_input(
                "Additional Strategic Notes (Optional)",
                placeholder="e.g. Must have experience building RAG architectures with 10k+ daily users..."
            )
        with col_ai_btn:
            st.write(" ")
            st.write(" ")
            if st.button("✨ Synthesize Enterprise JD", type="primary", use_container_width=True):
                if not pos_title.strip():
                    st.warning("Please enter a valid Job Position Title.")
                else:
                    with st.spinner("Synthesizing full enterprise Job Description with Groq LLM..."):
                        generated_jd = generate_enterprise_job_description(
                            title=pos_title,
                            department=pos_dept,
                            location_type=pos_loc,
                            experience_range=pos_exp,
                            tech_domain=pos_tech,
                            business_domain=pos_biz,
                            compensation=comp_type,
                            company_name="PragyanAI Venture Studio",
                            additional_notes=extra_context
                        )
                        st.session_state.draft_jd_markdown = generated_jd
                        st.session_state.jd_editor_rev += 1
                        st.success("Enterprise Job Description generated!")
                        st.rerun()

    elif ingest_mode == "📄 Upload Existing Document (PDF / DOCX)":
        uploaded_jd = st.file_uploader("Upload JD Document", type=["pdf", "docx"], key="publisher_file_upload")
        if uploaded_jd:
            if st.button("📥 Parse & Load into Editor", type="primary", use_container_width=True):
                raw_text = parse_pdf(uploaded_jd.read()) if uploaded_jd.name.endswith(".pdf") else parse_docx(uploaded_jd.read())
                if raw_text.strip():
                    st.session_state.draft_jd_markdown = raw_text
                    st.session_state.jd_editor_rev += 1
                    st.success("Document parsed and loaded into the workspace!")
                    st.rerun()

    else:
        pasted_text = st.text_area("Paste Raw JD Text:", height=180, placeholder="Paste JD requirements, responsibilities, competencies...", key="publisher_raw_paste")
        if st.button("📥 Load Raw Text into Editor", type="primary", use_container_width=True):
            if pasted_text.strip():
                st.session_state.draft_jd_markdown = pasted_text
                st.session_state.jd_editor_rev += 1
                st.success("Loaded into editor workspace!")
                st.rerun()

    # --------------------------------------------------------------------------
    # 3. Interactive Review, Edit & Dual Persistence (SQLite + ChromaDB)
    # --------------------------------------------------------------------------
    if st.session_state.draft_jd_markdown:
        st.markdown("---")
        st.subheader("3. Review, Fine-Tune & Publish Workspace")
        st.caption("Edit the Markdown specification directly. Once satisfied, click **'Publish & Index Job Position'** to save it to SQLite and vectorize it into ChromaDB.")

        col_edit_md, col_render_view = st.columns([1, 1])

        with col_edit_md:
            st.markdown("#### 📝 Editable Markdown Specification")
            rev_idx = st.session_state.jd_editor_rev
            edited_jd = st.text_area(
                "Live Markdown Editor",
                value=st.session_state.draft_jd_markdown,
                height=450,
                key=f"jd_live_editor_{rev_idx}"
            )
            st.session_state.draft_jd_markdown = edited_jd

        with col_render_view:
            st.markdown("#### 👁️ Rendered Candidate View")
            with st.container(height=450, border=True):
                st.markdown(st.session_state.draft_jd_markdown)

        col_publish_btn, col_pdf_export = st.columns([1, 1])

        with col_publish_btn:
            if st.button("🚀 Publish & Index Job Position to Database", type="primary", use_container_width=True):
                with st.spinner("Persisting specification to SQL database and vectorizing in ChromaDB..."):
                    # 1. Save to SQLite
                    saved_jd_record = sql_db.save_job_description(
                        title=pos_title,
                        department=pos_dept,
                        location_type=pos_loc,
                        content=st.session_state.draft_jd_markdown
                    )

                    # 2. Extract safe primary key
                    jd_pk = str(saved_jd_record.get("id")) if isinstance(saved_jd_record, dict) else str(getattr(saved_jd_record, "id", "jd_custom"))

                    # 3. Vectorize in ChromaDB for Semantic Search & RAG
                    chroma.upsert_jd(
                        jd_id=f"jd_{jd_pk}",
                        text=st.session_state.draft_jd_markdown,
                        metadata={
                            "title": pos_title,
                            "department": pos_dept,
                            "location_type": pos_loc,
                            "experience_range": pos_exp,
                            "tech_domain": pos_tech,
                            "business_domain": pos_biz
                        }
                    )

                    st.success(f"🎉 Position '{pos_title}' published and indexed successfully with ID: `jd_{jd_pk}`!")

        with col_pdf_export:
            jd_pdf_bytes = generate_pdf_report(st.session_state.draft_jd_markdown, title=f"JD - {pos_title}")
            st.download_button(
                label="📥 Download Publication PDF",
                data=jd_pdf_bytes,
                file_name=f"Job_Description_{pos_title.replace(' ', '_')}.pdf",
                mime="application/pdf",
                use_container_width=True
            )

# ==============================================================================
# TAB 2: ACTIVE POSITIONS INVENTORY
# ==============================================================================
with tab_inventory:
    st.header("Active Positions Inventory")
    session = SessionLocal()
    try:
        all_jds = session.query(JobDescription).order_by(JobDescription.created_at.desc()).all()
        if all_jds:
            df_inv = pd.DataFrame([{
                "ID": j.id,
                "Position Title": j.title,
                "Department": j.department,
                "Location": j.location_type,
                "Created At": j.created_at.strftime("%Y-%m-%d %H:%M") if j.created_at else "N/A"
            } for j in all_jds])
            st.dataframe(df_inv, use_container_width=True)

            selected_id = st.selectbox(
                "Inspect Full Position Specification:",
                options=[j.id for j in all_jds],
                format_func=lambda x: f"Position #{x}"
            )
            target_jd = next((j for j in all_jds if j.id == selected_id), None)
            if target_jd:
                with st.expander(f"📄 Full Specification: {target_jd.title}", expanded=True):
                    st.markdown(target_jd.content)
        else:
            st.info("No active job positions found. Publish a position in Tab 1.")
    finally:
        session.close()

# ==============================================================================
# TAB 3: CANDIDATE MATCHING & PIPELINE
# ==============================================================================
with tab_matcher:
    st.header("Candidate Matching & Pipeline Screening")
    st.caption("Match indexed candidate resumes against published position criteria.")

    session = SessionLocal()
    try:
        active_positions = session.query(JobDescription).all()
        all_resumes = session.query(Resume).all()
    finally:
        session.close()

    if active_positions and all_resumes:
        jd_choice = st.selectbox(
            "Select Position to Match Against:",
            options=[j.id for j in active_positions],
            format_func=lambda x: next((f"#{j.id} - {j.title} ({j.department})" for j in active_positions if j.id == x), str(x))
        )
        selected_jd_obj = next((j for j in active_positions if j.id == jd_choice), None)

        if st.button("🔍 Run Semantic Fit on Candidate Pool", type="primary"):
            results = []
            with st.spinner("Computing match scores across candidate resumes..."):
                for r in all_resumes:
                    cand_text = r.markdown_content or r.raw_content or ""
                    if cand_text.strip():
                        fit = match_cv_to_jd(cand_text, selected_jd_obj.content)
                        results.append({
                            "Candidate File": r.filename,
                            "User ID": r.user_id or "Anonymous",
                            "Match Score (%)": float(fit.get("match_score", 50)),
                            "Summary": fit.get("summary", ""),
                            "Strengths": ", ".join(fit.get("strengths", [])[:2]),
                            "Missing Gaps": ", ".join(fit.get("missing_keywords", [])[:3])
                        })

                results.sort(key=lambda x: x["Match Score (%)"], reverse=True)
                st.dataframe(pd.DataFrame(results), use_container_width=True)
    else:
        st.info("Requires at least one published Job Description and one indexed Candidate Resume.")
