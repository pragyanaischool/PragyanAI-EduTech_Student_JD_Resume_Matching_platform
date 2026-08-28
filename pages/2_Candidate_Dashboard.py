import streamlit as st
import json
import plotly.express as px
import pandas as pd
from datetime import datetime

from database.sql_models import JobDescription, Resume, Application
from database.sql_db import sql_db, SessionLocal
from database.chroma_db import chroma
from core.parsers import parse_pdf, parse_docx
from core.pdf_builder import generate_pdf_report
from core.prompt_engine import (
    build_markdown_resume,
    extract_resume_sections,
    update_resume_section,
    refine_resume_section,
    match_cv_to_jd,
    run_swot_analysis,
    optimize_ats_keywords,
    optimize_ats_resume,
    generate_cover_letter,
    generate_upskill_roadmap,
    generate_interview_questions,
    evaluate_interview_response,
)
from core.audio_engine import text_to_speech_audio, transcribe_audio_whisper
from core.search_tools import search_ddgs_web, search_youtube_videos

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

# Initialize Session State Variables
if "cand_cv" not in st.session_state:
    st.session_state.cand_cv = ""
if "cand_jd" not in st.session_state:
    st.session_state.cand_jd = ""
if "cv_revision" not in st.session_state:
    st.session_state.cv_revision = 0
if "refined_drafts" not in st.session_state:
    st.session_state.refined_drafts = {}
if "swot_result" not in st.session_state:
    st.session_state.swot_result = None
if "mock_questions" not in st.session_state:
    st.session_state.mock_questions = []
if "mock_q_idx" not in st.session_state:
    st.session_state.mock_q_idx = 0
if "mock_evals" not in st.session_state:
    st.session_state.mock_evals = {}

st.title("🎓 Candidate Career Acceleration Launchpad")
st.caption(f"Authenticated as: **{current_user.get('full_name') or current_user.get('email')}** ({current_user.get('email')})")

# ==============================================================================
# Pre-load Existing Candidate Resume if available
# ==============================================================================
session = SessionLocal()
try:
    if not st.session_state.cand_cv:
        existing_res = session.query(Resume).filter(Resume.user_id == current_user.get("id")).order_by(Resume.created_at.desc()).first()
        if existing_res:
            st.session_state.cand_cv = existing_res.markdown_content or existing_res.raw_content or ""
finally:
    session.close()

# ==============================================================================
# Navigation Tabs
# ==============================================================================
tab_cv, tab_match, tab_ats, tab_cover, tab_mock, tab_roadmap = st.tabs([
    "📝 1. Resume Builder & Studio",
    "🎯 2. JD Match & SWOT",
    "⚡ 3. ATS Keyword Optimizer",
    "✉️ 4. Smart Cover Letter",
    "🎙️ 5. Audio/Text Mock Interview",
    "🗺️ 6. Upskill Roadmap & Guides"
])

# ==============================================================================
# TAB 1: RESUME BUILDER & SECTION POLISH COPILOT
# ==============================================================================
with tab_cv:
    st.header("Step 1: Resume Ingestion, Section Refinement & PDF Export")
    
    col_in, col_preview = st.columns([1, 1])
    
    with col_in:
        st.subheader("Ingest Profile Data")
        upload_cv_file = st.file_uploader("Upload Existing Resume (PDF / DOCX)", type=["pdf", "docx"], key="cv_file_input")
        raw_notes_input = st.text_area("Or Paste Raw Profile / Career Notes", height=150, placeholder="Paste job history, key tech stack, projects, education...")
        
        c_gh, c_li = st.columns(2)
        github_input = c_gh.text_input("GitHub Profile URL", placeholder="https://github.com/...")
        linkedin_input = c_li.text_input("LinkedIn Profile URL", placeholder="https://linkedin.com/in/...")
        
        if st.button("🚀 Transform to ATS Markdown Resume", type="primary", use_container_width=True):
            raw_content = ""
            filename = "Parsed_Resume.pdf"
            if upload_cv_file:
                raw_content = parse_pdf(upload_cv_file.read()) if upload_cv_file.name.endswith(".pdf") else parse_docx(upload_cv_file.read())
                filename = upload_cv_file.name
            elif raw_notes_input.strip():
                raw_content = raw_notes_input.strip()
                filename = "Manual_Notes_Resume.txt"
                
            if raw_content.strip():
                with st.spinner("Refining profile into ATS Markdown with Groq LLM..."):
                    transformed_cv = build_markdown_resume(raw_content, github_input, linkedin_input)
                    st.session_state.cand_cv = transformed_cv
                    st.session_state.cv_revision += 1
                    st.session_state.refined_drafts = {}

                    sql_db.save_resume(
                        filename=filename,
                        raw_content=raw_content,
                        markdown_content=transformed_cv,
                        user_id=current_user.get("id")
                    )
                    st.success("Resume transformed and loaded into Section Copilot!")
                    st.rerun()
            else:
                st.warning("Please provide a resume file or paste profile notes.")

    with col_preview:
        st.subheader("Master Resume Preview & Export")
        if st.session_state.cand_cv:
            rev = st.session_state.cv_revision
            master_input = st.text_area(
                "Live Master Markdown Editor",
                value=st.session_state.cand_cv,
                height=250,
                key=f"master_resume_textarea_{rev}"
            )
            # Sync edits made directly in master text area
            if master_input != st.session_state.cand_cv:
                st.session_state.cand_cv = master_input
            
            pdf_bytes = generate_pdf_report(st.session_state.cand_cv, title="Curriculum Vitae")
            st.download_button(
                label="📥 Download Publication-Ready ATS PDF",
                data=pdf_bytes,
                file_name="Candidate_ATS_Resume.pdf",
                mime="application/pdf",
                type="primary",
                use_container_width=True
            )
        else:
            st.info("Ingest your resume on the left to activate preview, editing, and PDF download.")

    st.markdown("---")

    # Section Polish Copilot (Tabbed Interface)
    if st.session_state.cand_cv:
        st.subheader("🛠️ Section Polish Copilot (Action Verbs & Structured Skills)")
        st.caption("Auto-extracted sections from your master resume. Polish specific parts with AI and sync them back to the master resume.")

        extracted_sections = extract_resume_sections(st.session_state.cand_cv)
        rev = st.session_state.cv_revision

        t_sum, t_skl, t_exp, t_prj, t_edu = st.tabs([
            "📝 Summary",
            "⚡ Technical Skills",
            "💼 Professional Experience",
            "🚀 Key Projects",
            "🎓 Education & Certifications"
        ])

        sections_config = [
            (t_sum, "Executive Summary", "Polish Executive Summary"),
            (t_skl, "Technical Skills", "Categorize & Polish Technical Skills"),
            (t_exp, "Professional Experience", "Polish Experience (Google X-Y-Z)"),
            (t_prj, "Key Projects", "Polish Projects & Metrics"),
            (t_edu, "Education & Certifications", "Format Education & Certs")
        ]

        for tab_ui, sec_name, btn_label in sections_config:
            with tab_ui:
                c_sec_l, c_sec_r = st.columns(2)
                current_val = extracted_sections.get(sec_name, "")
                
                with c_sec_l:
                    st.markdown(f"**Current {sec_name}:**")
                    edited_input = st.text_area(
                        f"Edit Current {sec_name}",
                        value=current_val,
                        height=190,
                        key=f"in_sec_{sec_name}_{rev}"
                    )
                    
                    if st.button(f"✨ {btn_label}", key=f"btn_polish_{sec_name}_{rev}", type="primary"):
                        if edited_input.strip():
                            with st.spinner(f"Polishing {sec_name} with Groq AI..."):
                                polished_result = refine_resume_section(sec_name, edited_input)
                                st.session_state.refined_drafts[sec_name] = polished_result
                                st.rerun()
                        else:
                            st.warning(f"Content for {sec_name} is empty. Please enter or paste text.")

                with c_sec_r:
                    st.markdown(f"**AI Refined {sec_name}:**")
                    refined_val = st.session_state.refined_drafts.get(sec_name, "")
                    
                    refined_editor = st.text_area(
                        f"AI Refined {sec_name} Output",
                        value=refined_val,
                        height=190,
                        key=f"out_sec_{sec_name}_{rev}"
                    )
                    
                    if refined_editor.strip() and st.button(f"💾 Apply {sec_name} to Master Resume", key=f"apply_{sec_name}_{rev}"):
                        updated_full = update_resume_section(st.session_state.cand_cv, sec_name, refined_editor)
                        
                        # Update master resume text and increment revision counter
                        st.session_state.cand_cv = updated_full
                        st.session_state.cv_revision += 1
                        st.session_state.refined_drafts[sec_name] = refined_editor
                        
                        # Persist to database
                        sql_db.save_resume(
                            filename="Updated_Resume.md",
                            raw_content=updated_full,
                            markdown_content=updated_full,
                            user_id=current_user.get("id")
                        )
                        st.success(f"Successfully applied polished {sec_name} to Master Resume!")
                        st.rerun()

# ==============================================================================
# TAB 2: JD MATCH & SWOT ANALYSIS
# ==============================================================================
with tab_match:
    st.header("Step 2: Target JD Match & SWOT Diagnostic")
    
    col_jd_sel, col_jd_txt = st.columns([1, 2])
    
    with col_jd_sel:
        st.subheader("Select Target Position")
        session = SessionLocal()
        try:
            available_jds = session.query(JobDescription).all()
            jd_options = {f"{jd.title} ({jd.department} - {jd.location_type})": jd.content for jd in available_jds}
        finally:
            session.close()

        selected_jd_name = st.selectbox("Choose Indexed Job Description:", ["-- Custom / Paste Below --"] + list(jd_options.keys()))
        if selected_jd_name != "-- Custom / Paste Below --":
            st.session_state.cand_jd = jd_options[selected_jd_name]

    with col_jd_txt:
        st.subheader("Target Job Description Content")
        st.session_state.cand_jd = st.text_area(
            "Target JD Content",
            value=st.session_state.cand_jd,
            height=180,
            placeholder="Paste target job description requirements, responsibilities, and qualifications..."
        )

    if st.button("🎯 Run Deep SWOT & Compatibility Analysis", type="primary", use_container_width=True):
        if not st.session_state.cand_cv.strip():
            st.warning("Please complete Step 1 (Resume Ingestion) first.")
        elif not st.session_state.cand_jd.strip():
            st.warning("Please provide a target Job Description.")
        else:
            with st.spinner("Analyzing semantic fit, calculating match score, and generating SWOT matrix..."):
                st.session_state.swot_result = match_cv_to_jd(st.session_state.cand_cv, st.session_state.cand_jd)
                st.success("SWOT evaluation complete!")

    if st.session_state.swot_result:
        swot = st.session_state.swot_result
        st.markdown("---")
        
        c_score, c_summary = st.columns([1, 3])
        with c_score:
            score_val = float(swot.get("match_score", 0))
            fig_gauge = px.pie(
                values=[score_val, max(0, 100 - score_val)],
                names=["Match Fit", "Gap"],
                hole=0.7,
                color_discrete_sequence=["#2B6CB0", "#E2E8F0"]
            )
            fig_gauge.update_layout(showlegend=False, margin=dict(t=10, b=10, l=10, r=10), height=200)
            st.plotly_chart(fig_gauge, use_container_width=True)
            st.markdown(f"<h3 style='text-align: center; color: #2B6CB0;'>Match: {score_val}%</h3>", unsafe_allow_html=True)

        with c_summary:
            st.subheader("Executive Verdict")
            st.info(swot.get("summary", "Analysis completed."))
            if swot.get("missing_keywords"):
                st.markdown("**Critical Missing Keywords:**")
                st.write(", ".join([f"`{kw}`" for kw in swot.get("missing_keywords", [])]))

        # SWOT 2x2 Grid
        st.subheader("SWOT Diagnostic Matrix")
        s_col1, s_col2 = st.columns(2)
        
        with s_col1:
            st.success("💪 **Strengths (Direct Alignments)**")
            for item in swot.get("strengths", []):
                st.markdown(f"- {item}")
                
            st.info("🚀 **Opportunities (High-Value Leverage Points)**")
            for item in swot.get("opportunities", []):
                st.markdown(f"- {item}")

        with s_col2:
            st.warning("⚠️ **Weaknesses (Skill & Qualification Gaps)**")
            for item in swot.get("weaknesses", []):
                st.markdown(f"- {item}")

            st.error("🛑 **Threats (Hiring Risks / Mismatches)**")
            for item in swot.get("threats", []):
                st.markdown(f"- {item}")

# ==============================================================================
# TAB 3: ATS KEYWORD OPTIMIZER
# ==============================================================================
with tab_ats:
    st.header("Step 3: ATS Keyword Optimizer & Contextual Insertion")
    st.caption("Identify critical missing keywords and generate natural, contextual bullet points for your resume.")

    if st.button("⚡ Scan & Optimize ATS Keywords", type="primary", use_container_width=True):
        if not st.session_state.cand_cv.strip() or not st.session_state.cand_jd.strip():
            st.warning("Please ensure both your Resume (Step 1) and Target JD (Step 2) are loaded.")
        else:
            with st.spinner("Auditing ATS keyword frequency and generating bullet recommendations..."):
                st.session_state.ats_opt = optimize_ats_resume(st.session_state.cand_cv, st.session_state.cand_jd)
                st.success("ATS optimization analysis complete!")

    if "ats_opt" in st.session_state and st.session_state.ats_opt:
        ats_res = st.session_state.ats_opt
        
        c_ats1, c_ats2 = st.columns([1, 2])
        with c_ats1:
            st.metric("Estimated ATS Pass Score", f"{ats_res.get('ats_score_estimate', 75)}/100")
            st.markdown("**High-Priority Missing Terms:**")
            for kw in ats_res.get("critical_missing_keywords", []):
                st.markdown(f"- 🔴 `{kw}`")
        
        with c_ats2:
            st.subheader("Recommended Bullet Point Insertions")
            st.info(ats_res.get("keyword_density_advice", "Incorporate recommended technical keywords organically."))
            
            for idx, rec in enumerate(ats_res.get("recommended_bullet_insertions", []), start=1):
                with st.expander(f"Recommendation #{idx}: Target Section — {rec.get('target_section', 'Experience')}"):
                    st.code(rec.get("suggested_bullet", ""), language="markdown")

# ==============================================================================
# TAB 4: SMART COVER LETTER GENERATOR
# ==============================================================================
with tab_cover:
    st.header("Step 4: Smart Tailored Cover Letter")
    
    c_comp, c_gen = st.columns([2, 1])
    with c_comp:
        company_target = st.text_input("Target Organization / Company Name", value="Apex AI Labs")
    with c_gen:
        st.write(" ")
        st.write(" ")
        gen_cl_btn = st.button("✉️ Synthesize Tailored Cover Letter", type="primary", use_container_width=True)

    if gen_cl_btn:
        if not st.session_state.cand_cv.strip() or not st.session_state.cand_jd.strip():
            st.warning("Please ensure your Resume (Step 1) and Target JD (Step 2) are provided.")
        else:
            with st.spinner("Synthesizing personalized cover letter..."):
                st.session_state.cover_letter_text = generate_cover_letter(
                    st.session_state.cand_cv,
                    st.session_state.cand_jd,
                    company_name=company_target
                )
                st.success("Cover letter generated!")

    if "cover_letter_text" in st.session_state and st.session_state.cover_letter_text:
        st.session_state.cover_letter_text = st.text_area(
            "Generated Cover Letter",
            value=st.session_state.cover_letter_text,
            height=300
        )
        
        cl_pdf = generate_pdf_report(st.session_state.cover_letter_text, title=f"Cover Letter - {company_target}")
        st.download_button(
            label="📥 Download Cover Letter PDF",
            data=cl_pdf,
            file_name=f"Cover_Letter_{company_target.replace(' ', '_')}.pdf",
            mime="application/pdf",
            type="primary"
        )

# ==============================================================================
# TAB 5: AUDIO & TEXT MOCK INTERVIEW ROOM
# ==============================================================================
with tab_mock:
    st.header("Step 5: Voice & Text Interactive Mock Interview Room")
    st.caption("AI-conducted technical interviews with speech synthesis and Whisper audio transcription.")

    col_m1, col_m2 = st.columns([1, 1])
    with col_m1:
        round_selection = st.selectbox("Interview Format:", [
            "Round 1: Technical Systems Deep Dive",
            "Round 2: Architecture & Scalability",
            "Round 3: Leadership & Behavioral (STAR Method)"
        ])
    with col_m2:
        st.write(" ")
        st.write(" ")
        if st.button("🎙️ Initialize / Reset Mock Interview Session", type="primary", use_container_width=True):
            if not st.session_state.cand_cv.strip() or not st.session_state.cand_jd.strip():
                st.warning("Please provide your Resume and Target JD first.")
            else:
                with st.spinner("Analyzing profile and generating tailored scenario questions..."):
                    st.session_state.mock_questions = generate_interview_questions(
                        st.session_state.cand_jd,
                        st.session_state.cand_cv,
                        round_type=round_selection
                    )
                    st.session_state.mock_q_idx = 0
                    st.session_state.mock_evals = {}
                    st.success("Mock Interview initialized!")
                    st.rerun()

    if st.session_state.mock_questions:
        q_idx = st.session_state.mock_q_idx
        total_q = len(st.session_state.mock_questions)
        current_question = st.session_state.mock_questions[q_idx]

        st.markdown("---")
        st.subheader(f"Question {q_idx + 1} of {total_q}")
        st.markdown(f"### 🎯 *\"{current_question}\"*")

        # Audio Playback
        audio_stream = text_to_speech_audio(current_question)
        if audio_stream:
            st.audio(audio_stream, format="audio/mp3")

        st.markdown("#### Your Response:")
        resp_mode = st.radio("Response Input Mode:", ["Text Submission", "Voice Audio Upload"], horizontal=True)

        user_answer_text = ""
        if resp_mode == "Text Submission":
            user_answer_text = st.text_area("Type your technical explanation:", height=150, key=f"ans_text_{q_idx}")
        else:
            voice_file = st.file_uploader("Upload Voice Recording (WAV/MP3/M4A)", type=["wav", "mp3", "m4a"], key=f"voice_file_{q_idx}")
            if voice_file:
                with st.spinner("Transcribing speech with Groq Whisper..."):
                    user_answer_text = transcribe_audio_whisper(voice_file.read(), filename=voice_file.name)
                    st.text_area("Transcribed Answer:", value=user_answer_text, height=120)

        col_sub, col_next = st.columns([1, 1])
        with col_sub:
            if st.button("📝 Submit Answer for Evaluation", type="primary", use_container_width=True):
                if user_answer_text.strip():
                    with st.spinner("Grading response against JD requirements..."):
                        eval_data = evaluate_interview_response(current_question, user_answer_text, st.session_state.cand_jd)
                        st.session_state.mock_evals[q_idx] = eval_data
                        st.rerun()
                else:
                    st.warning("Please provide an answer before submitting.")

        with col_next:
            if q_idx < total_q - 1:
                if st.button("Next Question ➡️", use_container_width=True):
                    st.session_state.mock_q_idx += 1
                    st.rerun()

        # Display Evaluation for Current Question
        if q_idx in st.session_state.mock_evals:
            ev = st.session_state.mock_evals[q_idx]
            st.markdown("---")
            st.subheader("💡 Assessor Evaluation Feedback")
            
            c_e1, c_e2 = st.columns([1, 3])
            with c_e1:
                st.metric("Performance Score", f"{ev.get('score', 0)}/100")
                st.write(f"**Verdict:** {ev.get('verdict', 'Solid')}")
            
            with c_e2:
                st.success(f"**Strengths:** {', '.join(ev.get('strengths', []))}")
                st.warning(f"**Areas for Improvement:** {', '.join(ev.get('areas_for_improvement', []))}")
                st.info(f"**Ideal Senior Response:** {ev.get('ideal_response_summary', '')}")

# ==============================================================================
# TAB 6: UPSKILL ROADMAP & FREE GUIDES
# ==============================================================================
with tab_roadmap:
    st.header("Step 6: Tailored 4-Week Upskilling Roadmap")
    st.caption("Custom project milestones, web guides, and YouTube tutorials to close verified skill gaps.")

    missing_list = []
    if st.session_state.swot_result:
        missing_list = st.session_state.swot_result.get("missing_keywords", []) or st.session_state.swot_result.get("weaknesses", [])

    if st.button("🗺️ Synthesize 4-Week Project Roadmap", type="primary", use_container_width=True):
        target_role_title = "Target AI/Software Engineer"
        if not missing_list:
            missing_list = ["Vector Databases (ChromaDB)", "LangGraph State Machines", "High-Throughput FastAPI"]
            
        with st.spinner("Designing curriculum, querying DuckDuckGo and YouTube APIs..."):
            st.session_state.roadmap_data = generate_upskill_roadmap(missing_list[:5], target_role_title)
            st.success("Upskill Roadmap Generated!")

    if "roadmap_data" in st.session_state and st.session_state.roadmap_data:
        for week_plan in st.session_state.roadmap_data:
            with st.expander(f"📅 {week_plan.get('title', 'Week')} — Focus: {week_plan.get('focus_skill')}", expanded=True):
                col_w1, col_w2 = st.columns([1, 1])
                
                with col_w1:
                    st.markdown("**Learning Objectives:**")
                    for obj in week_plan.get("learning_objectives", []):
                        st.markdown(f"- {obj}")
                    
                    st.markdown("**Hands-On Capstone Project:**")
                    st.info(week_plan.get("hands_on_project", "Build reference prototype repository."))

                with col_w2:
                    st.markdown("🌐 **Web Tutorials & Reference Docs:**")
                    search_q = week_plan.get("search_queries", [week_plan.get("focus_skill")])[0]
                    web_articles = search_ddgs_web(search_q, max_results=2)
                    for art in web_articles:
                        st.markdown(f"- [{art['title']}]({art['href']})")

                    st.markdown("🎥 **Recommended Video Crash Courses:**")
                    yt_vids = search_youtube_videos(search_q, max_results=2)
                    for vid in yt_vids:
                        st.markdown(f"- 📺 [{vid['title']}]({vid['url']})")
