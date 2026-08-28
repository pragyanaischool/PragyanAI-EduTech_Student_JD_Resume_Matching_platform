import streamlit as st
import pandas as pd
from audio_recorder_streamlit import audio_recorder
from database.sql_db import sql_db
from database.sql_models import Resume, JobDescription
from core.parsers import parse_pdf, parse_docx
from core.prompt_engine import (
    build_markdown_resume,
    match_cv_to_jd,
    optimize_ats_resume,
    generate_cover_letter,
    create_interview_questions,
    evaluate_interview_answer,
    generate_learning_roadmap,
    refine_resume_section
)
from core.pdf_builder import generate_pdf_report
from core.audio_engine import generate_tts_audio, transcribe_audio
from core.search_tools import fetch_web_certifications, fetch_youtube_lectures

st.set_page_config(page_title="Candidate AI Career Launchpad", layout="wide", page_icon="🎓")

# Session Authorization Guard
if "auth_user" not in st.session_state or not st.session_state.auth_user:
    st.warning("Please sign in from the main portal to access the Candidate Hub.")
    st.stop()

if st.session_state.auth_user.get("role") != "candidate":
    st.error(f"Access Denied. Role '{st.session_state.auth_user.get('role').upper()}' is not authorized for Candidate Hub.")
    st.stop()

st.title("Candidate AI Career Launchpad")
st.caption("Build ATS-optimized resumes, run deep SWOT gap analysis, conduct voice mock interviews, and generate personalized learning roadmaps.")

# Session States
if "cand_cv" not in st.session_state:
    st.session_state.cand_cv = ""
if "cand_jd" not in st.session_state:
    st.session_state.cand_jd = ""
if "match_data" not in st.session_state:
    st.session_state.match_data = None
if "int_questions" not in st.session_state:
    st.session_state.int_questions = None
if "active_roadmap" not in st.session_state:
    st.session_state.active_roadmap = None

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "1. 📄 Resume Builder & Studio", 
    "2. 🎯 JD Match & SWOT Analysis", 
    "3. ⚡ ATS Resume Optimizer", 
    "4. ✉️ Smart Cover Letter", 
    "5. 🎙️ Voice & Text Mock Room", 
    "6. 🗺️ Upskill Roadmap & Courses"
])

session = sql_db.get_session()

# ----------------- TAB 1: RESUME BUILDER & STUDIO -----------------
with tab1:
    st.header("Step 1: Ingest, Polish & Export Resume")
    c1, c2 = st.columns([1, 1])
    
    with c1:
        st.subheader("Source Ingestion")
        f_cv = st.file_uploader("Upload Current CV (PDF/DOCX)", type=["pdf", "docx"], key="cand_cv_uploader")
        pasted_raw_cv = st.text_area("Or Paste Raw Profile Notes", height=150)
        
        ca, cb = st.columns(2)
        gh_url = ca.text_input("GitHub URL", placeholder="https://github.com/...")
        li_url = cb.text_input("LinkedIn URL", placeholder="https://linkedin.com/in/...")
        
        if st.button("Generate Professional Markdown Resume", type="primary", use_container_width=True):
            raw_text = ""
            filename = "Manual_Resume.txt"
            if f_cv:
                raw_text = parse_pdf(f_cv.read()) if f_cv.name.endswith(".pdf") else parse_docx(f_cv.read())
                filename = f_cv.name
            elif pasted_raw_cv:
                raw_text = pasted_raw_cv
                
            if raw_text.strip():
                with st.spinner("Refining profile into ATS Markdown with Groq..."):
                    st.session_state.cand_cv = build_markdown_resume(raw_text, gh_url, li_url)
                    user_id = st.session_state.auth_user["id"]
                    sql_db.save_resume(filename, raw_text, st.session_state.cand_cv, user_id=user_id)
                    st.success("Resume transformed to Markdown and saved to SQL.")
            else:
                st.warning("Please upload a file or paste raw text.")

    with c2:
        st.subheader("Live Markdown Editor & PDF Generator")
        if st.session_state.cand_cv:
            st.session_state.cand_cv = st.text_area("Live Markdown Content", value=st.session_state.cand_cv, height=350)
            
            with st.expander("Section Polish Copilot (Action Verbs & Grammar)"):
                sec_target = st.selectbox("Select Target Section", ["Executive Summary", "Technical Skills", "Professional Experience", "Key Projects"])
                sec_raw = st.text_area("Section Content to Enhance")
                if st.button("Enhance Section"):
                    enhanced_txt = refine_resume_section(sec_target, sec_raw)
                    st.code(enhanced_txt, language="markdown")
            
            pdf_bytes = generate_pdf_report(st.session_state.cand_cv, title="Curriculum Vitae")
            st.download_button(
                label="Download Formatted PDF",
                data=pdf_bytes,
                file_name="Candidate_Resume.pdf",
                mime="application/pdf",
                type="primary",
                use_container_width=True
            )
        else:
            st.info("Ingest your resume in the left panel to activate the live editor and PDF export.")

# ----------------- TAB 2: JD MATCH & SWOT ANALYSIS -----------------
with tab2:
    st.header("Step 2: Job Description Match & SWOT Diagnostic")
    col_jd1, col_jd2 = st.columns([1, 1])
    
    with col_jd1:
        st.subheader("Target Job Description")
        
        # Load from SQL Catalog or upload new
        sql_jds = session.query(JobDescription).all()
        jd_choice = st.selectbox("Select Existing Position from Database", ["-- New Upload / Custom --"] + [j.title for j in sql_jds])
        
        target_jd_text = ""
        if jd_choice != "-- New Upload / Custom --":
            selected_jd_obj = next(j for j in sql_jds if j.title == jd_choice)
            target_jd_text = selected_jd_obj.content
            st.text_area("Loaded Job Spec", value=target_jd_text, height=180, disabled=True)
        else:
            f_jd = st.file_uploader("Upload Target JD (PDF/DOCX)", type=["pdf", "docx"], key="cand_jd_uploader")
            p_jd = st.text_area("Or Paste Job Description Text", height=180)
            if f_jd:
                target_jd_text = parse_pdf(f_jd.read()) if f_jd.name.endswith(".pdf") else parse_docx(f_jd.read())
            elif p_jd:
                target_jd_text = p_jd
                
        if st.button("Run Full ATS Gap & SWOT Match", type="primary", use_container_width=True):
            if target_jd_text.strip() and st.session_state.cand_cv.strip():
                st.session_state.cand_jd = target_jd_text
                with st.spinner("Analyzing fit, calculating gaps, and generating SWOT matrix..."):
                    st.session_state.match_data = match_cv_to_jd(st.session_state.cand_cv, target_jd_text)
                    st.success("Analysis Complete!")
            else:
                st.warning("Ensure both a Resume (Tab 1) and a Job Description are loaded.")

    with col_jd2:
        st.subheader("Diagnostic Results")
        if st.session_state.match_data:
            m = st.session_state.match_data
            st.metric("ATS Match Score", f"{m.get('ats_score', 0)}%")
            
            sw = m.get("swot", {})
            sc1, sc2 = st.columns(2)
            sc1.success("**Strengths**\n" + "\n".join([f"- {s}" for s in sw.get("strengths", [])]))
            sc1.error("**Weaknesses**\n" + "\n".join([f"- {w}" for w in sw.get("weaknesses", [])]))
            sc2.info("**Opportunities**\n" + "\n".join([f"- {o}" for o in sw.get("opportunities", [])]))
            sc2.warning("**Threats / Risks**\n" + "\n".join([f"- {t}" for t in sw.get("threats", [])]))
            
            st.markdown("#### Section-by-Section Gap Breakdown")
            st.table(pd.DataFrame(m.get("section_gaps", [])))
        else:
            st.info("Run match analysis to display SWOT and gap diagnostics.")

# ----------------- TAB 3: ATS RESUME OPTIMIZER -----------------
with tab3:
    st.header("Step 3: ATS Organic Keyword Alignment")
    if st.session_state.match_data and st.session_state.cand_jd:
        missing_kw = st.session_state.match_data.get("missing_keywords", [])
        st.write(f"**Identified Missing Keywords:** `{', '.join(missing_kw)}`")
        
        if st.button("Auto-Inject Missing Keywords into Markdown Resume", type="primary"):
            with st.spinner("Rewriting resume bullet points with ATS keywords..."):
                optimized_cv = optimize_ats_resume(st.session_state.cand_cv, st.session_state.cand_jd, missing_kw)
                st.session_state.cand_cv = optimized_cv
                st.success("Resume updated with optimized terminology!")
                
        st.text_area("ATS-Optimized Markdown Resume", value=st.session_state.cand_cv, height=350)
    else:
        st.info("Please run the JD Match in Tab 2 first.")

# ----------------- TAB 4: SMART COVER LETTER -----------------
with tab4:
    st.header("Step 4: Tailored Cover Letter Generator")
    if st.session_state.cand_cv and st.session_state.cand_jd:
        if st.button("Generate Targeted Cover Letter", type="primary"):
            with st.spinner("Synthesizing achievement-matched cover letter..."):
                st.session_state.cand_cl = generate_cover_letter(st.session_state.cand_cv, st.session_state.cand_jd)
                
        if "cand_cl" in st.session_state:
            st.session_state.cand_cl = st.text_area("Your Cover Letter", value=st.session_state.cand_cl, height=280)
            cl_pdf = generate_pdf_report(st.session_state.cand_cl, title="Application Cover Letter")
            st.download_button(
                label="Download Cover Letter PDF",
                data=cl_pdf,
                file_name="Cover_Letter.pdf",
                mime="application/pdf",
                use_container_width=True
            )
    else:
        st.info("Load both a Resume and Job Description in prior tabs to generate cover letters.")

# ----------------- TAB 5: VOICE & TEXT MOCK ROOM -----------------
with tab5:
    st.header("Step 5: Voice & Text Interactive Mock Interview")
    if st.session_state.cand_jd:
        if st.button("Generate Custom Interview Questions", type="primary"):
            with st.spinner("Generating targeted HR, Skill, and Tech Architecture questions..."):
                st.session_state.int_questions = create_interview_questions(st.session_state.cand_jd)
                
        if st.session_state.int_questions:
            q_dict = st.session_state.int_questions
            all_q = (
                [("HR / Cultural", q) for q in q_dict.get("hr", [])] +
                [("Skill / Scenario", q) for q in q_dict.get("skill", [])] +
                [("Technical Deep Dive", q) for q in q_dict.get("tech", [])]
            )
            q_idx = st.selectbox("Select Question to Practice", range(len(all_q)), format_func=lambda i: f"[{all_q[i][0]}] {all_q[i][1]}")
            cat, question_text = all_q[q_idx]
            
            st.info(f"**Target Question:** {question_text}")
            
            if st.button("🔊 Listen to Question (AI Voice Audio)"):
                st.audio(generate_tts_audio(question_text), format="audio/mp3")
                
            ans_mode = st.radio("Response Mode", ["Speech / Microphone", "Text Input"], horizontal=True)
            candidate_answer_text = ""
            
            if ans_mode == "Speech / Microphone":
                st.write("Record your verbal answer:")
                raw_mic = audio_recorder(text="Click to record", recording_color="#e74c3c", neutral_color="#2b6cb0")
                if raw_mic:
                    with st.spinner("Transcribing speech with Groq Whisper..."):
                        candidate_answer_text = transcribe_audio(raw_mic)
                        st.info(f"**Transcribed Speech:** {candidate_answer_text}")
            else:
                candidate_answer_text = st.text_area("Type your detailed response here", height=120)
                
            if st.button("Submit Response for AI Grading", type="primary") and candidate_answer_text:
                with st.spinner("Evaluating response precision, structure, and STAR rubric..."):
                    eval_out = evaluate_interview_answer(question_text, candidate_answer_text, st.session_state.cand_jd)
                    st.metric("Performance Score", eval_out.get("score", "N/A"))
                    st.warning(f"**Critique & Missed Nuances:**\n{eval_out.get('critique')}")
                    st.success(f"**Model STAR Response:**\n{eval_out.get('star_answer')}")
    else:
        st.info("Load a target Job Description in Tab 2 to activate tailored mock interviews.")

# ----------------- TAB 6: UPSKILL ROADMAP & COURSES -----------------
with tab6:
    st.header("Step 6: Skill Gap Learning Roadmap & Online Courses")
    if st.session_state.match_data:
        gaps = st.session_state.match_data.get("missing_keywords", ["Python", "FastAPI"])
        
        col_r1, col_r2 = st.columns([1, 1])
        with col_r1:
            st.subheader("4-Week Project-Based Roadmap")
            if st.button("Generate Tailored 4-Week Plan", type="primary"):
                with st.spinner("Architecting learning curriculum with Groq..."):
                    st.session_state.active_roadmap = generate_learning_roadmap(gaps, st.session_state.cand_jd)
                    
            if st.session_state.active_roadmap:
                rm = st.session_state.active_roadmap
                st.markdown(f"**Focus Summary:** {rm.get('focus_summary')}")
                for week in rm.get("weekly_schedule", []):
                    with st.expander(f"{week.get('week')}: {week.get('topic')}", expanded=True):
                        st.write(f"**Project Deliverable:** {week.get('project')}")
                        st.caption(f"**Artifact:** {week.get('deliverable')}")

        with col_r2:
            st.subheader("Curated Free Learning Resources")
            selected_gap = st.selectbox("Select Target Skill to Explore", gaps)
            
            tab_web, tab_yt = st.tabs(["🎓 Certifications & Web Guides", "📺 YouTube Video Courses"])
            with tab_web:
                for cert in fetch_web_certifications(selected_gap):
                    st.markdown(f"- **[{cert['title']}]({cert['link']})**\n  {cert['snippet']}")
            with tab_yt:
                for yt in fetch_youtube_lectures(selected_gap):
                    st.markdown(f"- 📺 **[{yt['title']}]({yt['link']})** `(Duration: {yt['duration']})`")
    else:
        st.info("Run the JD Match in Tab 2 to detect missing skills and unlock roadmaps.")

session.close()
