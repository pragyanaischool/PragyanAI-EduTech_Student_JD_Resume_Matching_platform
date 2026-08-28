import streamlit as st
import plotly.express as px
from database.sql_models import JobDescription
from database.sql_db import SessionLocal
from core.audio_engine import text_to_speech_audio, transcribe_audio_whisper
from core.search_tools import search_ddgs_web, search_youtube_videos
from core.prompt_engine import (
    generate_multi_track_questions,
    evaluate_candidate_assessment_response,
)


def render_step6():
    st.header("Step 6: Interactive Placement Drive & Multi-Track Mock Simulator")
    st.caption("AI-driven placement simulation with multilingual voice/text rounds, automated evaluation, ideal senior answers, gap diagnosis, and live prep search.")

    if not st.session_state.get("cand_cv", "").strip():
        st.warning("⚠️ Please ensure your Master Resume is loaded in Step 1.")
        return

    # Ensure session state variables for Mock Drive
    if "drive_questions" not in st.session_state:
        st.session_state.drive_questions = []
    if "drive_q_idx" not in st.session_state:
        st.session_state.drive_q_idx = 0
    if "drive_evaluations" not in st.session_state:
        st.session_state.drive_evaluations = {}
    if "drive_overall_gaps" not in st.session_state:
        st.session_state.drive_overall_gaps = set()

    # ==============================================================================
    # 1. Round & Track Configuration Cockpit
    # ==============================================================================
    st.subheader("1. Placement Assessment Configuration")

    col_t1, col_t2, col_t3, col_t4 = st.columns([2, 1, 1, 1])

    with col_t1:
        selected_track = st.selectbox(
            "Evaluation Track:",
            [
                "Core CS & Software Engineering",
                "Data Structures & Algorithms",
                "Project Architecture Deep-Dive",
                "Internship & Work Experience",
                "HR & Behavioral Fit",
                "Aptitude & Verbal Reasoning"
            ],
            key="mock_track_selector"
        )

    with col_t2:
        selected_diff = st.selectbox(
            "Difficulty Tier:",
            ["Easy (Foundational)", "Medium (Core Practitioner)", "Advanced (Senior / Architect)"],
            key="mock_diff_selector"
        )

    with col_t3:
        selected_lang = st.selectbox(
            "Language:",
            ["English", "Hindi", "Kannada", "Tamil", "Telugu", "Spanish", "German"],
            key="mock_lang_selector"
        )

    with col_t4:
        q_count = st.number_input("Questions:", min_value=1, max_value=10, value=3, key="mock_q_count")

    # JD Context Selector
    col_jd_ctx, col_init_btn = st.columns([3, 1])
    with col_jd_ctx:
        session = SessionLocal()
        try:
            db_jds = session.query(JobDescription).all()
            jd_map = {f"#{j.id} - {j.title} ({j.department})": j.content for j in db_jds}
        finally:
            session.close()

        if "cand_jd" in st.session_state and st.session_state.cand_jd:
            jd_map["-- Current Active Target JD from Step 2 --"] = st.session_state.cand_jd

        selected_jd_choice = st.selectbox(
            "Context Job Description:",
            options=list(jd_map.keys()) if jd_map else ["-- Generic Senior Engineering Profile --"]
        )
        active_jd_content = jd_map.get(selected_jd_choice, st.session_state.get("cand_jd", "Software Engineering position."))

    with col_init_btn:
        st.write(" ")
        st.write(" ")
        if st.button("🚀 Start Assessment Round", type="primary", use_container_width=True):
            with st.spinner("Synthesizing tailored assessment questions with Groq LLM..."):
                diff_clean = selected_diff.split(" ")[0]
                questions = generate_multi_track_questions(
                    round_track=selected_track,
                    difficulty=diff_clean,
                    jd_text=active_jd_content,
                    resume_text=st.session_state.cand_cv,
                    language=selected_lang,
                    count=q_count
                )
                st.session_state.drive_questions = questions
                st.session_state.drive_q_idx = 0
                st.session_state.drive_evaluations = {}
                st.session_state.drive_current_track = selected_track
                st.session_state.drive_current_diff = diff_clean
                st.session_state.drive_current_lang = selected_lang
                st.success(f"Generated {len(questions)} questions for {selected_track}!")
                st.rerun()

    # ==============================================================================
    # 2. Interactive Interview Cockpit (Voice & Text)
    # ==============================================================================
    if st.session_state.drive_questions:
        q_idx = st.session_state.drive_q_idx
        total_q = len(st.session_state.drive_questions)
        q_data = st.session_state.drive_questions[q_idx]
        q_text = q_data.get("question", "")

        st.markdown("---")
        c_prog, c_meta = st.columns([3, 1])
        with c_prog:
            st.subheader(f"Question {q_idx + 1} of {total_q}")
            st.markdown(f"### 🎯 *\"{q_text}\"*")
        with c_meta:
            st.info(f"**Track:** {st.session_state.get('drive_current_track')}\n\n**Tier:** {st.session_state.get('drive_current_diff')}")

        # Text to Speech Audio Player
        lang_code = "hi" if st.session_state.get("drive_current_lang") == "Hindi" else "en"
        audio_bytes = text_to_speech_audio(q_text, lang=lang_code)
        if audio_bytes:
            st.audio(audio_bytes, format="audio/mp3")

        # Response Input Area (Text or Voice Recording)
        st.markdown("#### 🎙️ Your Response:")
        resp_type = st.radio("Response Mode:", ["Text Submission", "Voice Audio Upload"], horizontal=True, key=f"resp_mode_{q_idx}")

        answer_text = ""
        if resp_type == "Text Submission":
            answer_text = st.text_area(
                "Type your detailed explanation:",
                height=160,
                key=f"drive_ans_text_{q_idx}",
                placeholder="Explain your approach, trade-offs, architecture, and edge cases clearly..."
            )
        else:
            v_file = st.file_uploader(
                "Upload Spoken Audio (WAV / MP3 / M4A):",
                type=["wav", "mp3", "m4a"],
                key=f"drive_v_file_{q_idx}"
            )
            if v_file:
                with st.spinner("Transcribing speech with Groq Whisper..."):
                    transcribed = transcribe_audio_whisper(v_file.read(), filename=v_file.name)
                    st.session_state[f"whisper_transcript_{q_idx}"] = transcribed

            answer_text = st.text_area(
                "Transcribed Voice Response (Editable):",
                value=st.session_state.get(f"whisper_transcript_{q_idx}", ""),
                height=140,
                key=f"whisper_edit_{q_idx}"
            )

        col_submit, col_nav = st.columns([1, 1])
        with col_submit:
            if st.button("📝 Submit Response for AI Evaluation", type="primary", use_container_width=True):
                if answer_text.strip():
                    with st.spinner("Grading response, evaluating trade-offs, and diagnosing skill gaps..."):
                        evaluation = evaluate_candidate_assessment_response(
                            question=q_text,
                            user_response=answer_text,
                            track=st.session_state.get("drive_current_track", "Engineering"),
                            difficulty=st.session_state.get("drive_current_diff", "Medium"),
                            jd_text=active_jd_content,
                            resume_text=st.session_state.cand_cv,
                            language=st.session_state.get("drive_current_lang", "English")
                        )
                        st.session_state.drive_evaluations[q_idx] = evaluation

                        for g in evaluation.get("diagnosed_skill_gaps", []):
                            st.session_state.drive_overall_gaps.add(g)

                        st.success("Evaluation complete!")
                        st.rerun()
                else:
                    st.warning("Please provide an answer before submitting.")

        with col_nav:
            if q_idx < total_q - 1:
                if st.button("Next Question ➡️", use_container_width=True):
                    st.session_state.drive_q_idx += 1
                    st.rerun()
            else:
                if st.button("🔄 Restart Current Track", use_container_width=True):
                    st.session_state.drive_q_idx = 0
                    st.rerun()

        # ==============================================================================
        # 3. Comprehensive Evaluation Feedback & Ideal Response
        # ==============================================================================
        if q_idx in st.session_state.drive_evaluations:
            ev = st.session_state.drive_evaluations[q_idx]
            st.markdown("---")
            st.subheader("💡 Assessor Diagnostic & Evaluation Report")

            c_score, c_fb = st.columns([1, 3])
            with c_score:
                score_num = ev.get("score", 75)
                fig_sc = px.pie(
                    values=[score_num, max(0, 100 - score_num)],
                    names=["Score", "Room to Grow"],
                    hole=0.7,
                    color_discrete_sequence=["#2B6CB0", "#E2E8F0"]
                )
                fig_sc.update_layout(showlegend=False, margin=dict(t=10, b=10, l=10, r=10), height=180)
                st.plotly_chart(fig_sc, use_container_width=True)
                st.markdown(f"<h3 style='text-align: center; color: #2B6CB0;'>Score: {score_num}/100</h3>", unsafe_allow_html=True)
                st.caption(f"Verdict: **{ev.get('verdict', 'Solid')}**")

            with c_fb:
                st.success(f"**Strengths:** {', '.join(ev.get('strengths', ['Direct approach']))}")
                st.warning(f"**Areas for Improvement:** {', '.join(ev.get('areas_for_improvement', ['Quantify metrics']))}")

            # Ideal Senior Response & Better Phrasing
            t_ideal, t_better, t_gaps = st.tabs([
                "🌟 Ideal Senior Response",
                "✨ Optimized Phrasing of Your Answer",
                "🛑 Diagnosed Skill Gaps & Search Prep"
            ])

            with t_ideal:
                st.markdown("#### Senior Engineer Exemplary Answer:")
                st.info(ev.get("ideal_senior_response", "Detailed exemplary answer."))

            with t_better:
                st.markdown("#### How you could structure this answer better:")
                st.code(ev.get("better_phrased_candidate_answer", answer_text), language="markdown")

            with t_gaps:
                st.markdown("#### Diagnosed Gaps & Live Web Research:")
                gaps = ev.get("diagnosed_skill_gaps", [])
                if gaps:
                    st.write("**Identified Gaps:** " + ", ".join([f"`{g}`" for g in gaps]))

                search_queries = ev.get("recommended_search_queries", [])
                if search_queries:
                    st.markdown("**🌐 Live Tutorials & Web References:**")
                    for sq in search_queries:
                        web_links = search_ddgs_web(sq, max_results=2)
                        for wl in web_links:
                            st.markdown(f"- [{wl['title']}]({wl['href']})")

                    st.markdown("**🎥 Recommended Video Crash Courses:**")
                    for sq in search_queries:
                        vids = search_youtube_videos(sq, max_results=1)
                        for v in vids:
                            st.markdown(f"- 📺 [{v['title']}]({v['url']})")
