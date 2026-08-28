import streamlit as st
import plotly.express as px
from database.sql_models import JobDescription
from database.sql_db import SessionLocal
from core.parsers import parse_pdf, parse_docx
from core.prompt_engine import match_cv_to_jd, analyze_section_wise_match


def render_step2():
    st.header("Step 2: Target JD Upload, Section-Wise Matching & Deep SWOT")
    st.caption("Upload or select a target Job Description. Compare your resume with overall compatibility metrics, section-by-section fit, and a complete SWOT diagnostic matrix.")

    if not st.session_state.cand_cv.strip():
        st.warning("⚠️ Please complete Step 1 (Resume Ingestion) first.")
        return

    col_jd_sel, col_jd_txt = st.columns([1, 2])

    with col_jd_sel:
        st.subheader("1. Select or Upload JD")
        session = SessionLocal()
        try:
            available_jds = session.query(JobDescription).all()
            jd_options = {f"#{jd.id} - {jd.title} ({jd.department})": jd.content for jd in available_jds}
        finally:
            session.close()

        selected_jd_label = st.selectbox(
            "Choose Indexed JD:", 
            ["-- Select Indexed Position --"] + list(jd_options.keys())
        )
        if selected_jd_label != "-- Select Indexed Position --":
            st.session_state.cand_jd = jd_options[selected_jd_label]

        uploaded_jd_file = st.file_uploader(
            "Or Upload JD File (PDF / DOCX)", 
            type=["pdf", "docx"], 
            key="step2_jd_uploader"
        )
        if uploaded_jd_file:
            st.session_state.cand_jd = parse_pdf(uploaded_jd_file.read()) if uploaded_jd_file.name.endswith(".pdf") else parse_docx(uploaded_jd_file.read())

    with col_jd_txt:
        st.subheader("2. Target Job Description Content")
        st.session_state.cand_jd = st.text_area(
            "Target JD Content",
            value=st.session_state.cand_jd,
            height=200,
            placeholder="Paste target job responsibilities, tech stack, and qualifications here..."
        )

    if st.button("🎯 Run In-Depth Section-Wise Fit & SWOT Analysis", type="primary", use_container_width=True):
        if not st.session_state.cand_jd.strip():
            st.warning("Please provide target Job Description content.")
        else:
            with st.spinner("Analyzing semantic overlap, section alignment, and generating SWOT matrix..."):
                st.session_state.swot_result = match_cv_to_jd(st.session_state.cand_cv, st.session_state.cand_jd)
                st.session_state.section_match_result = analyze_section_wise_match(st.session_state.cand_cv, st.session_state.cand_jd)
                st.success("SWOT & Section Alignment Diagnostic Complete!")

    # ==========================================================================
    # Section-Wise Alignment Breakdown
    # ==========================================================================
    if "section_match_result" in st.session_state and st.session_state.section_match_result:
        sec_res = st.session_state.section_match_result
        st.markdown("---")
        st.subheader("📊 Section-by-Section Alignment Breakdown")

        sec_data = sec_res.get("section_breakdowns", {})
        if sec_data:
            sec_cols = st.columns(len(sec_data))
            for idx, (s_name, s_info) in enumerate(sec_data.items()):
                with sec_cols[idx]:
                    st.metric(s_name, f"{s_info.get('score', 0)}%", s_info.get("status", "Match"))
                    with st.expander("Details"):
                        st.markdown(f"**Alignments:** {s_info.get('alignment', 'Aligned')}")
                        st.markdown(f"**Gaps:** {s_info.get('gaps', 'None')}")

    # ==========================================================================
    # SWOT Matrix & Overall Match Gauge
    # ==========================================================================
    if st.session_state.swot_result:
        swot = st.session_state.swot_result
        st.markdown("---")
        st.subheader("🎯 Overall Fit & SWOT Matrix")

        c_gauge, c_verdict = st.columns([1, 2])
        with c_gauge:
            score_val = float(swot.get("match_score", 0))
            fig_gauge = px.pie(
                values=[score_val, max(0, 100 - score_val)],
                names=["Match Fit", "Gap"],
                hole=0.7,
                color_discrete_sequence=["#2B6CB0", "#E2E8F0"]
            )
            fig_gauge.update_layout(showlegend=False, margin=dict(t=10, b=10, l=10, r=10), height=180)
            st.plotly_chart(fig_gauge, use_container_width=True)
            st.markdown(f"<h3 style='text-align: center; color: #2B6CB0;'>Overall Fit: {score_val}%</h3>", unsafe_allow_html=True)

        with c_verdict:
            st.markdown("#### Executive Verdict")
            st.info(swot.get("summary", "Analysis completed."))
            if swot.get("missing_keywords"):
                st.markdown("**Missing Critical Keywords:**")
                st.write(", ".join([f"`{kw}`" for kw in swot.get("missing_keywords", [])]))

        # SWOT 2x2 Matrix Grid
        s_c1, s_c2 = st.columns(2)
        with s_c1:
            st.success("💪 **Strengths (Direct Alignments)**")
            for item in swot.get("strengths", []):
                st.markdown(f"- {item}")

            st.info("🚀 **Opportunities (High-Value Leverage Points)**")
            for item in swot.get("opportunities", []):
                st.markdown(f"- {item}")

        with s_c2:
            st.warning("⚠️ **Weaknesses (Identified Skill Gaps)**")
            for item in swot.get("weaknesses", []):
                st.markdown(f"- {item}")

            st.error("🛑 **Threats (Hiring Risks / Mismatches)**")
            for item in swot.get("threats", []):
                st.markdown(f"- {item}")
