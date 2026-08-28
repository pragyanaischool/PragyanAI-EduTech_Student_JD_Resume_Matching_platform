import streamlit as st
import pandas as pd
import json
import zipfile
import io
import uuid
from datetime import datetime, timedelta
import plotly.express as px

from database.sql_models import JobDescription, Resume, Application, User
from database.sql_db import sql_db, SessionLocal
from database.chroma_db import chroma
from core.parsers import parse_pdf, parse_docx, parse_url
from core.prompt_engine import (
    run_swot_analysis,
    match_cv_to_jd,
    screen_candidate_logistics,
    generate_interview_questions
)
from core.pdf_builder import generate_pdf_report

# ==============================================================================
# Page Configuration & Guardrails
# ==============================================================================
st.set_page_config(page_title="Employer Recruitment Hub", layout="wide", page_icon="🏢")

if "auth_user" not in st.session_state or not st.session_state.auth_user:
    st.warning("Please sign in from the main portal to access the Hiring Company Command Center.")
    st.stop()

current_user = st.session_state.auth_user
user_role = current_user.get("role", "company")

if user_role not in ["company", "admin"]:
    st.error(f"Access Denied. Your active role '{user_role.upper()}' is not authorized to access the Employer Portal.")
    st.stop()

st.title("🏢 Hiring Company Command Center")
st.caption(f"Authenticated as: **{current_user.get('full_name') or current_user.get('email')}** ({current_user.get('email')})")

# ==============================================================================
# Navigation Tabs
# ==============================================================================
tab_jd_vault, tab_prescreen, tab_ranking, tab_schedule, tab_pipeline = st.tabs([
    "📋 1. Job Studio & Resume Vault",
    "🛡️ 2. Logistics Pre-Screening",
    "🎯 3. Top-K Ranking & SWOT Matrix",
    "📅 4. SQL Interview Scheduler",
    "📊 5. Pipeline Telemetry & CSV Export"
])

# ==============================================================================
# TAB 1: JOB STUDIO & CANDIDATE RESUME VAULT
# ==============================================================================
with tab_jd_vault:
    st.header("Step 1: Publish Positions & Ingest Candidate Resumes")
    
    col_jd_create, col_resume_upload = st.columns([1, 1])

    # 1. Publish / Ingest Target Job Description
    with col_jd_create:
        st.subheader("Publish New Job Position (JD)")
        with st.form("create_jd_form", clear_on_submit=True):
            jd_title = st.text_input("Job Position Title", placeholder="e.g., Staff Autonomous AI Systems Engineer")
            c_dept, c_loc = st.columns(2)
            jd_department = c_dept.text_input("Department / Unit", value="Engineering & AI")
            jd_location = c_loc.selectbox("Work Location", ["Remote", "Hybrid (Bengaluru)", "Hybrid (Hyderabad)", "Onsite"])
            
            jd_input_mode = st.radio("JD Ingestion Source", ["Direct Text Paste", "Upload File (PDF/DOCX)"], horizontal=True)
            jd_raw_text = ""
            
            if jd_input_mode == "Direct Text Paste":
                jd_raw_text = st.text_area("Job Description Body", height=180, placeholder="Responsibilities, Qualifications, Tech Stack, Compensation...")
            else:
                jd_file = st.file_uploader("Upload JD Document", type=["pdf", "docx"], key="jd_file_uploader")
                if jd_file:
                    jd_raw_text = parse_pdf(jd_file.read()) if jd_file.name.endswith(".pdf") else parse_docx(jd_file.read())

            submit_jd = st.form_submit_button("Index JD into SQL & Vector Database", type="primary", use_container_width=True)

            if submit_jd:
                if not jd_title.strip() or not jd_raw_text.strip():
                    st.warning("Please provide both a position title and job description content.")
                else:
                    session = SessionLocal()
                    try:
                        new_jd = JobDescription(
                            title=jd_title.strip(),
                            department=jd_department.strip(),
                            location_type=jd_location,
                            content=jd_raw_text.strip()
                        )
                        session.add(new_jd)
                        session.commit()
                        session.refresh(new_jd)

                        # Upsert vector index in ChromaDB
                        chroma.upsert_jd(
                            doc_id=f"jd_{new_jd.id}",
                            text=new_jd.content,
                            metadata={"title": new_jd.title, "type": "jd", "sql_id": new_jd.id}
                        )
                        st.success(f"Position '{new_jd.title}' indexed successfully in SQL and ChromaDB vector store.")
                    except Exception as e:
                        session.rollback()
                        st.error(f"Error indexing JD: {str(e)}")
                    finally:
                        session.close()

    # 2. Bulk Ingest Resumes into Vault
    with col_resume_upload:
        st.subheader("Bulk Candidate Resume Ingestion")
        st.caption("Upload multiple PDFs/DOCXs or a ZIP archive containing candidate resumes.")
        
        uploaded_files = st.file_uploader(
            "Upload Candidate Resumes or ZIP Archive",
            type=["pdf", "docx", "zip"],
            accept_multiple_files=True,
            key="bulk_resume_uploader"
        )

        if st.button("📥 Parse & Vectorize Candidate Resumes", type="primary", use_container_width=True):
            if not uploaded_files:
                st.warning("Please select at least one file or ZIP bundle.")
            else:
                ingest_count = 0
                session = SessionLocal()
                try:
                    with st.spinner("Extracting text and generating dense vector embeddings..."):
                        for up_file in uploaded_files:
                            # Handle ZIP archive
                            if up_file.name.endswith(".zip"):
                                with zipfile.ZipFile(io.BytesIO(up_file.read())) as z:
                                    for z_name in z.namelist():
                                        if z_name.endswith(".pdf") or z_name.endswith(".docx"):
                                            file_bytes = z.read(z_name)
                                            raw_text = parse_pdf(file_bytes) if z_name.endswith(".pdf") else parse_docx(file_bytes)
                                            if raw_text.strip():
                                                base_filename = z_name.split("/")[-1]
                                                new_res = Resume(
                                                    filename=base_filename,
                                                    raw_content=raw_text,
                                                    markdown_content=raw_text
                                                )
                                                session.add(new_res)
                                                session.commit()
                                                session.refresh(new_res)

                                                chroma.upsert_resume(
                                                    doc_id=f"resume_{new_res.id}",
                                                    text=raw_text,
                                                    metadata={"filename": base_filename, "type": "resume", "sql_id": new_res.id}
                                                )
                                                ingest_count += 1
                            else:
                                # Handle individual PDF/DOCX
                                file_bytes = up_file.read()
                                raw_text = parse_pdf(file_bytes) if up_file.name.endswith(".pdf") else parse_docx(file_bytes)
                                if raw_text.strip():
                                    new_res = Resume(
                                        filename=up_file.name,
                                        raw_content=raw_text,
                                        markdown_content=raw_text
                                    )
                                    session.add(new_res)
                                    session.commit()
                                    session.refresh(new_res)

                                    chroma.upsert_resume(
                                        doc_id=f"resume_{new_res.id}",
                                        text=raw_text,
                                        metadata={"filename": up_file.name, "type": "resume", "sql_id": new_res.id}
                                    )
                                    ingest_count += 1

                    st.success(f"Successfully processed and indexed {ingest_count} candidate resumes.")
                except Exception as e:
                    session.rollback()
                    st.error(f"Error during ingestion: {str(e)}")
                finally:
                    session.close()

# ==============================================================================
# TAB 2: LOGISTICS PRE-SCREENING
# ==============================================================================
with tab_prescreen:
    st.header("Step 2: Candidate Logistics Verification & Feasibility Check")
    st.caption("Automated rule and LLM-based evaluation for notice period, salary expectations, and relocation constraints.")

    col_cand_info, col_req_info = st.columns(2)
    
    with col_cand_info:
        st.subheader("Candidate Provided Logistics")
        cand_name_input = st.text_input("Candidate Full Name", value="Aarav Sharma")
        cand_notice = st.selectbox("Current Notice Period", ["Immediate / 0 Days", "15 Days", "30 Days", "60 Days", "90 Days"])
        cand_curr_ctc = st.number_input("Current Annual Compensation (USD or Local equivalent)", value=110000, step=5000)
        cand_exp_ctc = st.number_input("Expected Annual Compensation", value=140000, step=5000)
        cand_loc_pref = st.selectbox("Location Preference / Relocation", ["Open to Relocate", "Remote Only", "Hybrid Only"])

    with col_req_info:
        st.subheader("Role Budget & Constraints")
        req_max_notice = st.selectbox("Maximum Acceptable Notice Period", ["30 Days", "60 Days", "90 Days"])
        req_budget_max = st.number_input("Role Budget Cap (Max Compensation)", value=150000, step=5000)
        req_work_mode = st.selectbox("Role Work Model Requirement", ["Flexible / Any", "Hybrid (Bengaluru)", "Onsite Only", "Remote Only"])

    if st.button("🛡️ Evaluate Logistics Feasibility", type="primary", use_container_width=True):
        candidate_logistics = {
            "name": cand_name_input,
            "notice_period": cand_notice,
            "current_ctc": cand_curr_ctc,
            "expected_ctc": cand_exp_ctc,
            "location_preference": cand_loc_pref
        }
        role_constraints = {
            "max_notice": req_max_notice,
            "budget_cap": req_budget_max,
            "work_mode": req_work_mode
        }

        with st.spinner("Evaluating constraints..."):
            prescreen_result = screen_candidate_logistics(candidate_logistics, role_constraints)
            
            st.markdown("---")
            status = prescreen_result.get("status", "PASS")
            confidence = prescreen_result.get("confidence_score", 90)
            summary = prescreen_result.get("summary", "Candidate meets operational screening requirements.")

            if status == "PASS":
                st.success(f"✅ **Screening Status: PASS** (Confidence: {confidence}%)")
            else:
                st.warning(f"⚠️ **Screening Status: {status}** (Confidence: {confidence}%)")

            st.info(f"**Assessor Justification:** {summary}")

# ==============================================================================
# TAB 3: TOP-K CANDIDATE MATCHING & SWOT MATRIX
# ==============================================================================
with tab_ranking:
    st.header("Step 3: Semantic Vector Matching & SWOT Diagnostic")
    st.caption("Rank candidate resumes against an open role using ChromaDB embeddings and Groq LLM SWOT analysis.")

    session = SessionLocal()
    try:
        available_jds = session.query(JobDescription).all()
        jd_dict = {f"#{jd.id} - {jd.title} ({jd.department})": jd for jd in available_jds}
    finally:
        session.close()

    if not jd_dict:
        st.info("No job descriptions found. Please publish or index a JD in Step 1.")
    else:
        selected_jd_label = st.selectbox("Select Target Job Description to Match Against:", list(jd_dict.keys()))
        active_jd = jd_dict[selected_jd_label]

        col_k1, col_k2 = st.columns([1, 1])
        with col_k1:
            top_k_val = st.slider("Number of Top Candidates to Retrieve (Top-K):", min_value=1, max_value=10, value=5)
        with col_k2:
            st.write(" ")
            st.write(" ")
            run_match_btn = st.button("🎯 Retrieve & Run Deep SWOT Ranking", type="primary", use_container_width=True)

        if run_match_btn:
            with st.spinner("Querying ChromaDB vector store and evaluating candidates..."):
                session = SessionLocal()
                try:
                    all_resumes = session.query(Resume).all()
                    
                    if not all_resumes:
                        st.warning("Candidate vault is empty. Please upload resumes in Step 1.")
                    else:
                        match_records = []
                        
                        for r in all_resumes:
                            # Evaluate match using LLM SWOT engine
                            swot_eval = run_swot_analysis(r.raw_content, active_jd.content)
                            score = float(swot_eval.get("match_score", 50.0))
                            
                            cand_name = r.filename.replace(".pdf", "").replace(".docx", "").replace("_", " ")
                            
                            match_records.append({
                                "resume_id": r.id,
                                "candidate_name": cand_name,
                                "filename": r.filename,
                                "match_score": score,
                                "summary": swot_eval.get("summary", ""),
                                "swot": swot_eval,
                                "raw_content": r.raw_content
                            })

                        # Sort descending by score and slice Top-K
                        match_records.sort(key=lambda x: x["match_score"], reverse=True)
                        st.session_state.matched_candidates = match_records[:top_k_val]
                        st.session_state.active_matching_jd = active_jd
                        st.success(f"Evaluated {len(all_resumes)} resumes. Top {min(top_k_val, len(match_records))} candidates ranked below.")
                finally:
                    session.close()

        # Display Top-K Candidates Matrix
        if "matched_candidates" in st.session_state and st.session_state.matched_candidates:
            ranked_list = st.session_state.matched_candidates
            
            st.markdown("---")
            st.subheader(f"Top {len(ranked_list)} Ranked Candidates for '{st.session_state.active_matching_jd.title}'")

            # Plotly Bar Chart of Top-K
            df_chart = pd.DataFrame([{
                "Candidate": c["candidate_name"],
                "Match Score (%)": c["match_score"]
            } for c in ranked_list])
            
            fig_bar = px.bar(
                df_chart,
                x="Candidate",
                y="Match Score (%)",
                color="Match Score (%)",
                color_continuous_scale="Blues",
                title="Candidate Fit Distribution"
            )
            fig_bar.update_layout(yaxis_range=[0, 100])
            st.plotly_chart(fig_bar, use_container_width=True)

            # Detailed Candidate Cards with SWOT Matrix
            for idx, cand in enumerate(ranked_list, start=1):
                with st.expander(f"Rank #{idx}: {cand['candidate_name']} — Match Score: {cand['match_score']}%"):
                    c_swot = cand["swot"]
                    
                    st.info(f"**Executive Verdict:** {cand['summary']}")
                    
                    swot_col1, swot_col2 = st.columns(2)
                    with swot_col1:
                        st.success("💪 **Strengths (Direct Alignments)**")
                        for s in c_swot.get("strengths", []):
                            st.markdown(f"- {s}")
                            
                        st.info("🚀 **Opportunities (Growth & Leverage Areas)**")
                        for o in c_swot.get("opportunities", []):
                            st.markdown(f"- {o}")

                    with swot_col2:
                        st.warning("⚠️ **Weaknesses (Skill Gaps)**")
                        for w in c_swot.get("weaknesses", []):
                            st.markdown(f"- {w}")

                        st.error("🛑 **Threats (Hiring Risks)**")
                        for t in c_swot.get("threats", []):
                            st.markdown(f"- {t}")

                    st.markdown("---")
                    
                    # Quick action to save to Application Pipeline
                    col_save_app, col_view_cv = st.columns([1, 1])
                    with col_save_app:
                        if st.button(f"➕ Shortlist {cand['candidate_name']} for Scheduling", key=f"shortlist_{cand['resume_id']}"):
                            session = SessionLocal()
                            try:
                                new_app = Application(
                                    candidate_name=cand["candidate_name"],
                                    candidate_email=f"{cand['candidate_name'].lower().replace(' ', '.')}@example.com",
                                    jd_id=st.session_state.active_matching_jd.id,
                                    match_score=cand["match_score"],
                                    swot_json=json.dumps(cand["swot"]),
                                    stage="Pre-Screen Passed"
                                )
                                session.add(new_app)
                                session.commit()
                                st.success(f"{cand['candidate_name']} added to Pipeline & Scheduler queue.")
                            except Exception as e:
                                session.rollback()
                                st.error(f"Error creating application: {str(e)}")
                            finally:
                                session.close()

                    with col_view_cv:
                        pdf_rep = generate_pdf_report(cand["raw_content"], title=f"Candidate CV - {cand['candidate_name']}")
                        st.download_button(
                            label=f"📄 Download Clean CV ({cand['candidate_name']})",
                            data=pdf_rep,
                            file_name=f"{cand['candidate_name'].replace(' ', '_')}_CV.pdf",
                            mime="application/pdf",
                            key=f"dl_cv_{cand['resume_id']}"
                        )

# ==============================================================================
# TAB 4: SQL INTERVIEW SCHEDULER
# ==============================================================================
with tab_schedule:
    st.header("Step 4: Interview Dispatch & SQL Calendar Scheduler")
    st.caption("Advance candidate hiring stages, schedule interview rounds, and generate virtual meeting rooms.")

    session = SessionLocal()
    try:
        pipeline_apps = session.query(Application).all()
        app_lookup = {f"#{a.id} - {a.candidate_name} ({a.stage} | Score: {a.match_score}%)": a.id for a in pipeline_apps}
    finally:
        session.close()

    if not app_lookup:
        st.info("No applications in pipeline. Shortlist candidates from Step 3 (Top-K Matching) to schedule interviews.")
    else:
        col_sel_app, col_form = st.columns([1, 2])
        
        with col_sel_app:
            st.subheader("Select Candidate")
            chosen_app_label = st.selectbox("Candidate in Queue:", list(app_lookup.keys()))
            selected_app_id = app_lookup[chosen_app_label]

        with col_form:
            st.subheader("Interview Details")
            session = SessionLocal()
            try:
                target_app = session.query(Application).filter(Application.id == selected_app_id).first()
                if target_app:
                    with st.form("interview_schedule_form"):
                        new_stage = st.selectbox(
                            "Pipeline Stage",
                            ["Applied", "Pre-Screen Passed", "Scheduled", "Hired", "Rejected"],
                            index=["Applied", "Pre-Screen Passed", "Scheduled", "Hired", "Rejected"].index(target_app.stage) if target_app.stage in ["Applied", "Pre-Screen Passed", "Scheduled", "Hired", "Rejected"] else 0
                        )
                        
                        interview_type = st.selectbox("Interview Format", [
                            "Round 1: AI Technical Assessment",
                            "Round 2: Live System Architecture Deep Dive",
                            "Round 3: Hiring Manager & Leadership Fit",
                            "Final Executive Offer Discussion"
                        ])
                        
                        col_date, col_time = st.columns(2)
                        int_date = col_date.date_input("Interview Date", value=datetime.today() + timedelta(days=2))
                        int_time = col_time.time_input("Interview Time", value=datetime.now().time())
                        
                        default_meeting_link = target_app.meeting_link or f"https://meet.jit.si/Interview_{uuid.uuid4().hex[:8]}"
                        meeting_url = st.text_input("Virtual Meeting Room URL", value=default_meeting_link)
                        
                        notes = st.text_area("Agenda Notes for Interviewers", value=target_app.agenda_notes or "Probe concurrency optimization, vector search scaling, and system latency.")
                        
                        submit_schedule = st.form_submit_button("💾 Save Schedule & Update SQL Record", type="primary", use_container_width=True)

                        if submit_schedule:
                            combined_datetime = datetime.combine(int_date, int_time)
                            target_app.stage = new_stage
                            target_app.interview_type = interview_type
                            target_app.interview_time = combined_datetime
                            target_app.meeting_link = meeting_url
                            target_app.agenda_notes = notes
                            session.commit()
                            st.success(f"Interview for {target_app.candidate_name} scheduled successfully!")
                            st.rerun()
            finally:
                session.close()

# ==============================================================================
# TAB 5: PIPELINE TELEMETRY & CSV EXPORT
# ==============================================================================
with tab_pipeline:
    st.header("Step 5: Pipeline Telemetry & CSV Export")
    st.caption("Live operational dashboard of all active candidate pipelines and one-click data export.")

    session = SessionLocal()
    try:
        all_apps = session.query(Application).all()
        
        if not all_apps:
            st.info("Zero active applications in the recruitment pipeline.")
        else:
            table_data = []
            for app in all_apps:
                jd_title = app.jd.title if app.jd else "General Pool"
                int_time_str = app.interview_time.strftime("%Y-%m-%d %H:%M") if app.interview_time else "Not Scheduled"
                table_data.append({
                    "Application ID": app.id,
                    "Candidate Name": app.candidate_name,
                    "Email": app.candidate_email,
                    "Applied Position": jd_title,
                    "Fit Score (%)": app.match_score,
                    "Current Stage": app.stage,
                    "Interview Type": app.interview_type or "N/A",
                    "Interview Schedule": int_time_str,
                    "Meeting Link": app.meeting_link or "N/A"
                })

            df_pipeline = pd.DataFrame(table_data)
            
            # Metrics Row
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Total In Pipeline", len(df_pipeline))
            m2.metric("Pre-Screen Passed", len(df_pipeline[df_pipeline["Current Stage"] == "Pre-Screen Passed"]))
            m3.metric("Interviews Scheduled", len(df_pipeline[df_pipeline["Current Stage"] == "Scheduled"]))
            m4.metric("Offers / Hired", len(df_pipeline[df_pipeline["Current Stage"] == "Hired"]))

            st.markdown("---")
            st.subheader("Active Pipeline Table")
            st.dataframe(df_pipeline, use_container_width=True)

            # CSV Download Button
            csv_buffer = io.StringIO()
            df_pipeline.to_csv(csv_buffer, index=False)
            csv_bytes = csv_buffer.getvalue().encode("utf-8")

            col_csv, col_spacer = st.columns([1, 2])
            with col_csv:
                st.download_button(
                    label="📊 Export Pipeline Shortlist (CSV)",
                    data=csv_bytes,
                    file_name="PragyanAI_Recruitment_Pipeline_Report.csv",
                    mime="text/csv",
                    type="primary",
                    use_container_width=True
                )
    finally:
        session.close()
