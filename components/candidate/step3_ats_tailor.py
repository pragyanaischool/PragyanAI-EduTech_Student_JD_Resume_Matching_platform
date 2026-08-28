import streamlit as st
from database.sql_db import sql_db
from core.pdf_builder import generate_pdf_report
from core.prompt_engine import auto_tailor_cv_for_jd


def render_step3(current_user: dict):
    st.header("Step 3: ATS Score Optimization, Interactive Tailoring & Residual Gap Roadmap")
    st.caption("Auto-align your master resume to the target JD ATS parameters, inspect proposed modifications, accept/edit changes, and build a roadmap for remaining skill gaps.")

    if not st.session_state.cand_cv.strip() or not st.session_state.cand_jd.strip():
        st.warning("⚠️ Please ensure both your Resume (Step 1) and Target JD (Step 2) are loaded.")
        return

    if st.button("⚡ Generate ATS Auto-Tailored CV & Diff Analysis", type="primary", use_container_width=True):
        with st.spinner("Synthesizing tailored Markdown resume, computing diffs, and auditing missing skills..."):
            tailor_res = auto_tailor_cv_for_jd(st.session_state.cand_cv, st.session_state.cand_jd)
            st.session_state.tailor_result = tailor_res
            st.session_state.tailor_candidate_md = tailor_res.get("tailored_resume_markdown", st.session_state.cand_cv)
            st.success("Auto-tailoring complete!")

    if "tailor_result" in st.session_state and st.session_state.tailor_result:
        t_data = st.session_state.tailor_result
        st.markdown("---")

        c_m1, c_m2 = st.columns([1, 2])
        with c_m1:
            st.metric("Projected ATS Score", f"{t_data.get('projected_ats_score', 90)}/100")
            st.success("Optimized for technical keyword density and ATS parsers.")

        with c_m2:
            st.markdown("#### 🔍 Proposed Phrasing & Content Modifications")
            changes = t_data.get("proposed_changes", [])
            if changes:
                for idx, chg in enumerate(changes, 1):
                    with st.expander(f"Change #{idx}: {chg.get('section', 'General')} — {chg.get('rationale', 'Improvement')}"):
                        st.markdown(f"**Original:** `{chg.get('original_phrase')}`")
                        st.markdown(f"**Tailored:** `{chg.get('modified_phrase')}`")
            else:
                st.info("Direct keyword alignments already incorporated into the drafted resume.")

        # ======================================================================
        # Interactive Accept / Edit Workspace
        # ======================================================================
        st.markdown("---")
        st.subheader("✍️ Interactive Final Tailored CV Editor")
        st.caption("Review the tailored version below. You can customize the Markdown directly before accepting and saving it as your active master resume.")

        c_edit_l, c_edit_r = st.columns([1, 1])

        with c_edit_l:
            st.markdown("#### 📝 Tailored Markdown Workspace")
            edited_tailored_md = st.text_area(
                "Tailored Markdown Editor",
                value=st.session_state.get("tailor_candidate_md", st.session_state.cand_cv),
                height=380,
                key="tailored_md_editor_box"
            )
            st.session_state.tailor_candidate_md = edited_tailored_md

            if st.button("✅ Accept & Set as Master Resume", type="primary", use_container_width=True):
                st.session_state.cand_cv = edited_tailored_md
                st.session_state.master_rev += 1
                sql_db.save_resume(
                    filename="ATS_Tailored_Resume.md",
                    raw_content=edited_tailored_md,
                    markdown_content=edited_tailored_md,
                    user_id=current_user.get("id")
                )
                st.success("Accepted! Tailored resume is now saved as your Master Resume.")
                st.rerun()

        with c_edit_r:
            st.markdown("#### 👁️ Live Rendered Presentation & Download")
            with st.container(height=380, border=True):
                st.markdown(st.session_state.tailor_candidate_md)

            pdf_bytes = generate_pdf_report(st.session_state.tailor_candidate_md, title="ATS Tailored Resume")
            st.download_button(
                label="📥 Download Tailored ATS PDF",
                data=pdf_bytes,
                file_name="Target_Tailored_ATS_Resume.pdf",
                mime="application/pdf",
                type="primary",
                use_container_width=True
            )

        # ======================================================================
        # Residual Major Missing Skills & Practical Workouts
        # ======================================================================
        st.markdown("---")
        st.subheader("🏋️ Residual Skill Gaps & Practical Workouts")
        st.caption("Skills required by the target JD that cannot be truthfully claimed in your CV without hands-on implementation.")

        residual_skills = t_data.get("residual_missing_skills", [])
        if residual_skills:
            for item in residual_skills:
                with st.container(border=True):
                    col_sk1, col_sk2 = st.columns([1, 2])
                    with col_sk1:
                        st.markdown(f"### 🛑 `{item.get('skill')}`")
                        st.caption(f"Severity: **{item.get('severity', 'High')}**")
                        st.warning(item.get("gap_reason", "Not detected in career history."))
                    with col_sk2:
                        st.markdown("**🛠️ Actionable Implementation Workout:**")
                        st.info(item.get("quick_workout", "Build an isolated proof-of-concept repository."))
        else:
            st.success("No critical unaddressed skill gaps detected for this position!")
