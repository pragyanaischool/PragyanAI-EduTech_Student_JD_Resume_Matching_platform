import streamlit as st
import pandas as pd
from database.sql_models import JobDescription
from database.sql_db import SessionLocal
from core.prompt_engine import analyze_multi_jd_skill_gap
from core.search_tools import search_ddgs_web, search_youtube_videos


def render_step5():
    st.header("Step 5: Collective Multi-JD Skill Matrix & 8-Week Upskill Plan")
    st.caption("Identify market-wide skill gaps across all active job positions and build an 8-week curriculum with documentation and video crash courses.")

    if not st.session_state.cand_cv.strip():
        st.warning("⚠️ Please ensure your Master Resume is loaded in Step 1.")
        return

    session = SessionLocal()
    try:
        all_jds = session.query(JobDescription).all()
        jds_pool = [{"id": j.id, "title": j.title, "content": j.content} for j in all_jds]
    finally:
        session.close()

    if not jds_pool:
        st.info("No job descriptions available to construct aggregate market matrix.")
        return

    if st.button("🗺️ Compute Industry Skill Matrix & 8-Week Blueprint", type="primary", use_container_width=True):
        with st.spinner("Auditing collective market demand and structuring curriculum..."):
            matrix_res = analyze_multi_jd_skill_gap(st.session_state.cand_cv, jds_pool)
            st.session_state.multi_skill_matrix = matrix_res
            st.success("Aggregate market skill analysis complete!")

    if "multi_skill_matrix" in st.session_state and st.session_state.multi_skill_matrix:
        res = st.session_state.multi_skill_matrix
        st.markdown("---")

        c_sc1, c_sc2 = st.columns([1, 2])
        with c_sc1:
            st.metric("Aggregate Market Readiness", f"{res.get('market_readiness_score', 75)}/100")
        with c_sc2:
            st.markdown("**Core Verified Competencies:**")
            st.write(", ".join([f"`{c}`" for c in res.get("core_competencies_matched", [])]))

        # ======================================================================
        # High-Frequency Missing Skills Table
        # ======================================================================
        st.subheader("🔥 High-Frequency Missing Skills Across All JDs")
        missing_skills = res.get("high_frequency_missing_skills", [])
        if missing_skills:
            df_gaps = pd.DataFrame(missing_skills)
            st.dataframe(df_gaps, use_container_width=True)

        # ======================================================================
        # 8-Week Strategic Upskill Curriculum
        # ======================================================================
        st.markdown("---")
        st.subheader("📅 8-Week Project-Based Upskilling Blueprint")

        curriculum = res.get("eight_week_upskill_curriculum", [])
        for phase_idx, phase in enumerate(curriculum, 1):
            with st.expander(f"📌 {phase.get('phase', f'Phase {phase_idx}')}", expanded=True):
                col_p1, col_p2 = st.columns([1, 1])

                with col_p1:
                    st.markdown("**Core Skills Covered:**")
                    st.write(", ".join([f"`{s}`" for s in phase.get("skills", [])]))
                    st.markdown("**Hands-On Capstone Deliverable:**")
                    st.info(phase.get("deliverable_project", "Build prototype repository."))

                with col_p2:
                    search_term = phase.get("recommended_search_term", phase.get("skills", ["AI Engineer"])[0])
                    st.markdown(f"🌐 **Reference Tutorials (`{search_term}`):**")
                    articles = search_ddgs_web(search_term, max_results=2)
                    for art in articles:
                        st.markdown(f"- [{art['title']}]({art['href']})")

                    st.markdown("🎥 **Recommended Crash Courses:**")
                    vids = search_youtube_videos(search_term, max_results=2)
                    for v in vids:
                        st.markdown(f"- 📺 [{v['title']}]({v['url']})")
