import streamlit as st
import pandas as pd
import json
import uuid
from datetime import datetime, date, time
from core.parsers import parse_pdf, parse_docx, parse_zip
from database.sql_db import sql_db
from database.sql_models import JobDescription, Application
from database.chroma_db import chroma
from core.prompt_engine import match_cv_to_jd, parse_and_structure_jd, evaluate_pre_screening

st.set_page_config(page_title="Hiring Company Console", layout="wide", page_icon="🏢")

# Session Authorization Guard
if "auth_user" not in st.session_state or not st.session_state.auth_user:
    st.warning("Please sign in from the main portal to access the Employer Command Center.")
    st.stop()

if st.session_state.auth_user.get("role") != "company":
    st.error(f"Access Denied. Role '{st.session_state.auth_user.get('role').upper()}' is not authorized for Employer Console.")
    st.stop()

st.title("Hiring Company Command Center")
st.caption("Publish positions, screen candidate logistics, rank candidate vaults with semantic search, inspect SWOT diagnostics, and schedule interviews.")

session = sql_db.get_session()

if "emp_jd_text" not in st.session_state:
    st.session_state.emp_jd_text = ""
if "emp_raw_candidates" not in st.session_state:
    st.session_state.emp_raw_candidates = []
if "emp_ranked_list" not in st.session_state:
    st.session_state.emp_ranked_list = []

tab_jd, tab_screen, tab_rank, tab_sched, tab_export = st.tabs([
    "1. 📋 Job Position Studio", 
    "2. 🛡️ Candidate Pre-Screening", 
    "3. 📊 Top-K Rank & SWOT Diagnostics", 
    "4. 📅 SQL Interview Scheduler",
    "5. 📤 Pipeline Export (CSV)"
])

# ----------------- TAB 1: JOB POSITION STUDIO -----------------
with tab_jd:
    st.header("Step 1: Ingest Job Position & Upload Candidate Resumes")
    c1, c2 = st.columns([1, 1])
    
    with c1:
        st.subheader("Job Description Ingestion")
        jd_title_in = st.text_input("Position Title", value="Senior Generative AI Architect")
        dept_in = st.text_input("Department", value="Core AI Engineering")
        loc_type_in = st.selectbox("Work Arrangement", ["Remote", "Hybrid", "Onsite"])
        raw_jd_paste = st.text_area("Job Description Requirements", height=180, value="Seeking Lead AI Engineer with LangChain, LangGraph, Groq, ChromaDB, and Python production experience.")
        
        if st.button("Save & Index Position", type="primary", use_container_width=True):
            if raw_jd_paste.strip():
                st.session_state.emp_jd_text = raw_jd_paste
                new_jd = JobDescription(
                    title=jd_title_in,
                    department=dept_in,
                    location_type=loc_type_in,
                    content=raw_jd_paste
                )
                session.add(new_jd)
                session.commit()
                session.refresh(new_jd)
                
                chroma.upsert_jd(
                    doc_id=f"jd_{new_jd.id}",
                    text=raw_jd_paste,
                    metadata={"title": jd_title_in, "type": "jd", "sql_id": new_jd.id}
                )
                st.success(f"Position '{jd_title_in}' saved in SQL and indexed into ChromaDB.")

    with c2:
        st.subheader("Bulk Candidate Resume Intake")
        intake_mode = st.radio("Resume Intake Mode", ["Individual PDF / DOCX Files", "ZIP Archive Bundle"], horizontal=True)
        
        if intake_mode == "Individual PDF / DOCX Files":
            files = st.file_uploader("Upload Resumes", type=["pdf", "docx"], accept_multiple_files=True, key="emp_files")
            if files and st.button("Process & Vectorize Resumes", type="primary", use_container_width=True):
                st.session_state.emp_raw_candidates = []
                for f in files:
                    txt = parse_pdf(f.read()) if f.name.endswith(".pdf") else parse_docx(f.read())
                    st.session_state.emp_raw_candidates.append({"filename": f.name, "text": txt})
                st.success(f"Successfully processed {len(files)} resumes.")
        else:
            z_file = st.file_uploader("Upload ZIP File Containing Resumes", type=["zip"], key="emp_zip")
            if z_file and st.button("Unpack & Vectorize ZIP Bundle", type="primary", use_container_width=True):
                st.session_state.emp_raw_candidates = parse_zip(z_file.read())
                st.success(f"Unpacked {len(st.session_state.emp_raw_candidates)} candidate documents from ZIP.")

# ----------------- TAB 2: CANDIDATE PRE-SCREENING -----------------
with tab_screen:
    st.header("Step 2: Candidate Logistics & Compensation Pre-Screen")
    st.caption("Screen notice period, compensation alignment, relocation feasibility, and core experience before running deep diagnostics.")
    
    col_sc1, col_sc2 = st.columns(2)
    with col_sc1:
        ps_name = st.text_input("Candidate Full Name", "Aarav Sharma")
        ps_c_ctc = st.text_input("Current CTC ($ / ₹)", "$115,000")
        ps_e_ctc = st.text_input("Expected CTC ($ / ₹)", "$145,000")
        ps_notice = st.slider("Notice Period (Days)", min_value=0, max_value=90, value=30, step=5)
        ps_buyout = st.checkbox("Notice Period Buyout Allowed by Employer?", value=True)
        
    with col_sc2:
        ps_c_loc = st.text_input("Candidate Location", "Bengaluru, India")
        ps_j_loc = st.text_input("Target Office Location", "Bengaluru, India")
        ps_reloc = st.checkbox("Willing to Relocate if required?", value=True)
        ps_skill_notes = st.text_area("Key Experience Summary in Required Stack", "5+ years in Python, built LangGraph multi-agent systems and low-latency Groq inference pipelines.")
        
        if st.button("Run Pre-Screen Logic Validation", type="primary", use_container_width=True):
            with st.spinner("AI assessing logistical constraints..."):
                ps_eval = evaluate_pre_screening(
                    ps_c_ctc, ps_e_ctc, ps_notice, ps_buyout, ps_c_loc, ps_j_loc, ps_reloc, ps_skill_notes
                )
                if ps_eval.get("is_qualified"):
                    st.success(f"**Status:** {ps_eval.get('status')}")
                else:
                    st.error(f"**Status:** {ps_eval.get('status')}")
                st.write(f"**Recruiter Notes:** {ps_eval.get('summary')}")
                if ps_eval.get("risk_flags"):
                    st.warning(f"**Flagged Items:** {', '.join(ps_eval.get('risk_flags'))}")

# ----------------- TAB 3: TOP-K RANK & SWOT DIAGNOSTICS -----------------
with tab_rank:
    st.header("Step 3: Semantic Match, Top-K Ranking & SWOT Matrix")
    
    if st.session_state.emp_raw_candidates and st.session_state.emp_jd_text:
        if st.button("Rank All Ingested Candidates with Semantic Scoring", type="primary"):
            with st.spinner("Evaluating candidate pool and computing SWOT matrices..."):
                ranked = []
                for cand in st.session_state.emp_raw_candidates:
                    res = match_cv_to_jd(cand["text"], st.session_state.emp_jd_text)
                    ranked.append({
                        "Candidate File": cand["filename"],
                        "Match Score": res.get("ats_score", 50.0),
                        "Strengths": "; ".join(res.get("swot", {}).get("strengths", [])),
                        "Weaknesses": "; ".join(res.get("swot", {}).get("weaknesses", [])),
                        "Missing Skills": ", ".join(res.get("missing_keywords", [])),
                        "Raw SWOT": res.get("swot", {})
                    })
                st.session_state.emp_ranked_list = sorted(ranked, key=lambda x: x["Match Score"], reverse=True)
                st.success("Candidate pool ranked successfully.")
                
    if st.session_state.emp_ranked_list:
        df_rank = pd.DataFrame(st.session_state.emp_ranked_list)[["Candidate File", "Match Score", "Strengths", "Weaknesses"]]
        st.dataframe(df_rank, use_container_width=True)
        
        st.markdown("---")
        st.subheader("Deep Candidate SWOT Matrix Inspection")
        selected_cand_file = st.selectbox("Select Candidate for Deep Diagnostic", [r["Candidate File"] for r in st.session_state.emp_ranked_list])
        selected_cand_data = next(r for r in st.session_state.emp_ranked_list if r["Candidate File"] == selected_cand_file)
        
        swot_obj = selected_cand_data["Raw SWOT"]
        c_sw1, c_sw2 = st.columns(2)
        c_sw1.success("**Strengths**\n" + "\n".join([f"- {s}" for s in swot_obj.get("strengths", [])]))
        c_sw1.error("**Weaknesses**\n" + "\n".join([f"- {w}" for w in swot_obj.get("weaknesses", [])]))
        c_sw2.info("**Opportunities**\n" + "\n".join([f"- {o}" for o in swot_obj.get("opportunities", [])]))
        c_sw2.warning("**Threats / Risks**\n" + "\n".join([f"- {t}" for t in swot_obj.get("threats", [])]))
    else:
        st.info("Ingest position requirements and resumes in Tab 1 to run semantic ranking.")

# ----------------- TAB 4: SQL INTERVIEW SCHEDULER -----------------
with tab_sched:
    st.header("Step 4: Interview Scheduling & Database Logger")
    
    if st.session_state.emp_ranked_list:
        candidate_options = [f"{c['Candidate File']} (Score: {c['Match Score']}%)" for c in st.session_state.emp_ranked_list]
        sel_idx = st.selectbox("Select Shortlisted Candidate", range(len(candidate_options)), format_func=lambda i: candidate_options[i])
        target_cand_record = st.session_state.emp_ranked_list[sel_idx]
        
        col_sch1, col_sch2 = st.columns(2)
        with col_sch1:
            round_type = st.selectbox("Interview Stage", [
                "Round 1: AI Technical Assessment",
                "Round 2: Systems Architecture Deep Dive",
                "Round 3: Behavioral & Executive Fit"
            ])
            cand_email_in = st.text_input("Candidate Email Address", value="candidate@domain.com")
            sched_date = st.date_input("Interview Date", min_value=date.today())
            sched_time = st.time_input("Interview Time", value=time(14, 30))
            
        with col_sch2:
            sched_agenda = st.text_area(
                "Agenda & Focus Questions",
                value=f"Focus on probing: {target_cand_record.get('Missing Skills')}\nEvaluate core strengths: {target_cand_record.get('Strengths')[:100]}...",
                height=120
            )
            
            if st.button("Save Interview Schedule to Database", type="primary", use_container_width=True):
                combined_dt = datetime.combine(sched_date, sched_time)
                virtual_meet_link = f"https://meet.jit.si/Interview_{uuid.uuid4().hex[:8]}"
                
                new_app = Application(
                    candidate_name=target_cand_record["Candidate File"].split(".")[0],
                    candidate_email=cand_email_in,
                    match_score=target_cand_record["Match Score"],
                    swot_json=json.dumps(target_cand_record["Raw SWOT"]),
                    stage="Scheduled",
                    interview_type=round_type,
                    interview_time=combined_dt,
                    meeting_link=virtual_meet_link,
                    agenda_notes=sched_agenda
                )
                session.add(new_app)
                session.commit()
                st.success(f"Interview scheduled for {cand_email_in} and logged in SQL.")
                st.info(f"**Virtual Meeting Link:** [{virtual_meet_link}]({virtual_meet_link})")
                
        st.markdown("---")
        st.subheader("All Scheduled Interviews in Database")
        db_scheduled = session.query(Application).filter(Application.stage == "Scheduled").all()
        if db_scheduled:
            sched_table_data = [{
                "Candidate": a.candidate_name,
                "Email": a.candidate_email,
                "Round": a.interview_type,
                "Scheduled Time": a.interview_time.strftime("%Y-%m-%d %H:%M") if a.interview_time else "N/A",
                "Meeting Link": a.meeting_link
            } for a in db_scheduled]
            st.dataframe(pd.DataFrame(sched_table_data), use_container_width=True)
    else:
        st.info("Rank candidates in Tab 3 before scheduling interview rounds.")

# ----------------- TAB 5: PIPELINE EXPORT (CSV) -----------------
with tab_export:
    st.header("Step 5: Export Ranked Shortlist & Candidate Diagnostics")
    if st.session_state.emp_ranked_list:
        df_export = pd.DataFrame(st.session_state.emp_ranked_list)[["Candidate File", "Match Score", "Strengths", "Weaknesses", "Missing Skills"]]
        csv_bytes = df_export.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="Download Candidate Evaluations CSV",
            data=csv_bytes,
            file_name="Candidate_Evaluations_Report.csv",
            mime="text/csv",
            type="primary",
            use_container_width=True
        )
        st.dataframe(df_export, use_container_width=True)
    else:
        st.info("Run candidate ranking in Tab 3 to unlock CSV export.")

session.close()
