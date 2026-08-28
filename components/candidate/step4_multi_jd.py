import streamlit as st
import pandas as pd
import plotly.express as px
from database.sql_models import JobDescription
from database.sql_db import SessionLocal
from core.pdf_builder import generate_pdf_report
from core.prompt_engine import match_cv_to_jd, generate_cover_letter


def render_step4():
    st.header("Step 4: Multi-JD Match, Ranking & Batch Cover Letter Generation")
    st.caption("Match your final resume across all available job descriptions, rank position compatibility, and generate tailored cover letters.")

    if not st.session_state.cand_cv.strip():
        st.warning("⚠️ Please ensure your Master Resume is loaded in Step 1.")
        return

    session = SessionLocal()
    try:
        all_jds = session.query(JobDescription).all()
        jds_pool = [
            {
                "id": j.id, 
                "title": j.title, 
                "department": j.department, 
                "location_type": j.location_type, 
                "content": j.content
            } for j in all_jds
        ]
    finally:
        session.close()

    if not jds_pool:
        st.info("No job descriptions found in the database. Please publish JDs from the Hiring Portal.")
        return

    st.markdown(f"Found **{len(jds_pool)}** open positions in the platform index.")

    if st.button("🚀 Evaluate & Rank Against All JDs", type="primary", use_container_width=True):
        ranked_results = []
        with st.spinner("Evaluating candidate fit against all active positions..."):
            for jd_item in jds_pool:
                match_eval = match_cv_to_jd(st.session_state.cand_cv, jd_item["content"])
                ranked_results.append({
                    "jd_id": jd_item["id"],
                    "position_title": jd_item["title"],
                    "department": jd_item["department"],
                    "location": jd_item["location_type"],
                    "match_score": float(match_eval.get("match_score", 50.0)),
                    "summary": match_eval.get("summary", ""),
                    "swot": match_eval,
                    "jd_content": jd_item["content"]
                })

            ranked_results.sort(key=lambda x: x["match_score"], reverse=True)
            st.session_state.multi_jd_rankings = ranked_results
            st.success(f"Successfully ranked {len(ranked_results)} positions!")

    if "multi_jd_rankings" in st.session_state and st.session_state.multi_jd_rankings:
        rankings = st.session_state.multi_jd_rankings
        st.markdown("---")
        st.subheader("🏆 Ranked Compatibility Matrix")

        df_rank = pd.DataFrame([{
            "Rank": f"#{idx}",
            "Position": r["position_title"],
            "Department": r["department"],
            "Location": r["location"],
            "Match Fit (%)": r["match_score"]
        } for idx, r in enumerate(rankings, 1)])

        st.dataframe(df_rank, use_container_width=True)

        fig_bar = px.bar(
            df_rank,
            x="Position",
            y="Match Fit (%)",
            color="Match Fit (%)",
            color_continuous_scale="Blues",
            title="Candidate Alignment Across Open Positions"
        )
        fig_bar.update_layout(yaxis_range=[0, 100])
        st.plotly_chart(fig_bar, use_container_width=True)

        # ======================================================================
        # Batch Tailored Cover Letter Generator
        # ======================================================================
        st.markdown("---")
        st.subheader("✉️ Generate Tailored Cover Letter for Selected Position")

        jd_selection_options = {
            f"#{r['jd_id']} - {r['position_title']} ({r['match_score']}% Match)": r for r in rankings
        }
        chosen_jd_key = st.selectbox(
            "Select Target Position for Cover Letter:", 
            list(jd_selection_options.keys())
        )
        selected_record = jd_selection_options[chosen_jd_key]

        c_org, c_cl_gen = st.columns([2, 1])
        with c_org:
            org_name = st.text_input("Company / Organization Name", value="Hiring Team")
        with c_cl_gen:
            st.write(" ")
            st.write(" ")
            if st.button("✉️ Synthesize Tailored Cover Letter", type="primary", use_container_width=True):
                with st.spinner("Generating tailored cover letter..."):
                    cl_text = generate_cover_letter(
                        st.session_state.cand_cv, 
                        selected_record["jd_content"], 
                        company_name=org_name
                    )
                    st.session_state.active_cover_letter = cl_text
                    st.success("Cover letter generated!")

        if "active_cover_letter" in st.session_state and st.session_state.active_cover_letter:
            st.session_state.active_cover_letter = st.text_area(
                "Generated Cover Letter", 
                value=st.session_state.active_cover_letter, 
                height=280
            )
            cl_pdf = generate_pdf_report(st.session_state.active_cover_letter, title=f"Cover Letter - {org_name}")
            st.download_button(
                label="📥 Download Cover Letter PDF",
                data=cl_pdf,
                file_name=f"Cover_Letter_{selected_record['position_title'].replace(' ', '_')}.pdf",
                mime="application/pdf",
                type="primary"
            )
