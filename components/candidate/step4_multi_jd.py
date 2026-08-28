import streamlit as st
import pandas as pd
import plotly.express as px
from database.sql_models import JobDescription
from database.sql_db import sql_db, SessionLocal
from database.chroma_db import chroma
from core.parsers import parse_pdf, parse_docx
from core.pdf_builder import generate_pdf_report
from core.prompt_engine import match_cv_to_jd, generate_cover_letter


def _extract_id(result_obj, default_val: str) -> str:
    """Helper to safely extract ID whether result_obj is dict, ORM object, int, or string."""
    if isinstance(result_obj, dict):
        return str(result_obj.get("id", default_val))
    if hasattr(result_obj, "id"):
        return str(result_obj.id)
    if isinstance(result_obj, (int, str)):
        return str(result_obj)
    return str(default_val)


def render_step4():
    st.header("Step 4: Multi-JD Match, Ranking & Batch Cover Letter Generation")
    st.caption("Upload multiple JDs, select from indexed database positions, rank position compatibility, and generate tailored cover letters.")

    if not st.session_state.cand_cv.strip():
        st.warning("⚠️ Please ensure your Master Resume is loaded in Step 1.")
        return

    # ==============================================================================
    # 1. Multi-JD Ingestion Hub (Upload Batch / Manual Paste / DB Select)
    # ==============================================================================
    st.subheader("1. Job Descriptions Selection & Batch Upload Hub")

    tab_upload, tab_db, tab_paste = st.tabs([
        "📁 1. Batch Upload JD Files",
        "🗄️ 2. Select / Extract from Database",
        "📝 3. Quick Paste JDs"
    ])

    # Initialize transient multi-JD buffer in session state
    if "custom_jds_pool" not in st.session_state:
        st.session_state.custom_jds_pool = []

    with tab_upload:
        st.markdown("#### Upload Multiple Job Descriptions (PDF / DOCX)")
        uploaded_jd_files = st.file_uploader(
            "Upload one or more JD documents:",
            type=["pdf", "docx"],
            accept_multiple_files=True,
            key="multi_jd_files_uploader"
        )

        col_up_dept, col_up_loc, col_up_save = st.columns([1, 1, 1])
        with col_up_dept:
            upload_dept = st.text_input("Default Department / Team", value="Engineering", key="up_jd_dept")
        with col_up_loc:
            upload_loc = st.selectbox("Location Type", ["Remote", "Hybrid", "On-site"], key="up_jd_loc")
        with col_up_save:
            save_to_db_toggle = st.checkbox("💾 Save & Index to Database", value=True, help="Automatically save parsed JDs into SQLite & ChromaDB.")

        if st.button("📥 Parse & Ingest Uploaded JDs", type="primary", use_container_width=True):
            if uploaded_jd_files:
                added_count = 0
                for idx, file_obj in enumerate(uploaded_jd_files):
                    raw_text = parse_pdf(file_obj.read()) if file_obj.name.endswith(".pdf") else parse_docx(file_obj.read())
                    if raw_text.strip():
                        jd_title = file_obj.name.rsplit(".", 1)[0].replace("_", " ").replace("-", " ").title()
                        
                        # Add to active evaluation pool
                        jd_entry = {
                            "id": f"upload_{len(st.session_state.custom_jds_pool) + 1}",
                            "title": jd_title,
                            "department": upload_dept,
                            "location_type": upload_loc,
                            "content": raw_text
                        }
                        st.session_state.custom_jds_pool.append(jd_entry)
                        added_count += 1

                        # Save to SQL & Vector Database if enabled
                        if save_to_db_toggle:
                            try:
                                saved_jd = sql_db.save_job_description(
                                    title=jd_title,
                                    department=upload_dept,
                                    location_type=upload_loc,
                                    content=raw_text
                                )
                                jd_pk = _extract_id(saved_jd, f"up_{idx}_{added_count}")
                                chroma.upsert_jd(
                                    jd_id=f"jd_{jd_pk}",
                                    text=raw_text,
                                    metadata={
                                        "title": jd_title,
                                        "department": upload_dept,
                                        "location_type": upload_loc
                                    }
                                )
                            except Exception as e:
                                pass

                st.success(f"Successfully parsed and loaded {added_count} job descriptions!")
                st.rerun()
            else:
                st.warning("Please select at least one JD file to upload.")

    with tab_db:
        st.markdown("#### Select and Extract from Existing Database Positions")
        session = SessionLocal()
        try:
            db_jds = session.query(JobDescription).all()
            db_pool = [
                {
                    "id": f"db_{j.id}",
                    "db_pk": j.id,
                    "title": j.title,
                    "department": j.department,
                    "location_type": j.location_type,
                    "content": j.content
                } for j in db_jds
            ]
        finally:
            session.close()

        if db_pool:
            db_options_map = {
                f"#{j['db_pk']} - {j['title']} ({j['department']} | {j['location_type']})": j for j in db_pool
            }
            selected_db_keys = st.multiselect(
                "Choose JDs from Database to evaluate:",
                options=list(db_options_map.keys()),
                default=list(db_options_map.keys())
            )
            
            if st.button("➕ Add Selected DB JDs to Active Pool", use_container_width=True):
                for k in selected_db_keys:
                    item = db_options_map[k]
                    if not any(x.get("id") == item["id"] for x in st.session_state.custom_jds_pool):
                        st.session_state.custom_jds_pool.append(item)
                st.success(f"Loaded {len(selected_db_keys)} database positions into active pool!")
                st.rerun()
        else:
            st.info("No job descriptions found in database. Use Tab 1 to upload files and save them to the database.")

    with tab_paste:
        st.markdown("#### Quick Paste Job Description")
        c_p_title, c_p_dept = st.columns(2)
        paste_title = c_p_title.text_input("Job Title", value="Senior AI Systems Engineer", key="paste_jd_title")
        paste_dept = c_p_dept.text_input("Department", value="Engineering", key="paste_jd_dept")
        paste_content = st.text_area("Paste JD Requirements & Responsibilities:", height=150, key="paste_jd_text")
        paste_save_db = st.checkbox("💾 Save Quick-Pasted JD to Database", value=False)

        if st.button("➕ Add Pasted JD to Evaluation Pool", use_container_width=True):
            if paste_content.strip():
                p_entry = {
                    "id": f"paste_{len(st.session_state.custom_jds_pool) + 1}",
                    "title": paste_title,
                    "department": paste_dept,
                    "location_type": "Remote",
                    "content": paste_content.strip()
                }
                st.session_state.custom_jds_pool.append(p_entry)

                if paste_save_db:
                    try:
                        saved_jd = sql_db.save_job_description(
                            title=paste_title,
                            department=paste_dept,
                            location_type="Remote",
                            content=paste_content.strip()
                        )
                        jd_pk = _extract_id(saved_jd, f"paste_{len(st.session_state.custom_jds_pool)}")
                        chroma.upsert_jd(
                            jd_id=f"jd_{jd_pk}",
                            text=paste_content.strip(),
                            metadata={"title": paste_title, "department": paste_dept, "location_type": "Remote"}
                        )
                    except Exception as e:
                        pass
                st.success(f"Added '{paste_title}' to pool!")
                st.rerun()
            else:
                st.warning("Please paste job description text.")

    # ==============================================================================
    # 2. Active Evaluation Pool Overview
    # ==============================================================================
    st.markdown("---")
    active_jds = st.session_state.custom_jds_pool

    c_cnt, c_clr = st.columns([3, 1])
    with c_cnt:
        st.subheader(f"2. Active JDs for Ranking ({len(active_jds)} Positions Ready)")
    with c_clr:
        if active_jds and st.button("🗑️ Clear Pool", use_container_width=True):
            st.session_state.custom_jds_pool = []
            st.session_state.multi_jd_rankings = []
            st.rerun()

    if not active_jds:
        st.warning("No JDs currently in the active pool. Upload files in Tab 1, select DB positions in Tab 2, or paste in Tab 3.")
        return

    # Display active pool badges
    jd_badges = [f"**{j['title']}** ({j.get('department', 'General')})" for j in active_jds]
    st.write("Current Pool: " + " • ".join(jd_badges))

    # ==============================================================================
    # 3. Multi-JD Matching & Ranking Pipeline
    # ==============================================================================
    if st.button("🚀 Evaluate & Rank Against All JDs in Pool", type="primary", use_container_width=True):
        ranked_results = []
        with st.spinner(f"Evaluating candidate resume against {len(active_jds)} positions with Groq LLM..."):
            for jd_item in active_jds:
                match_eval = match_cv_to_jd(st.session_state.cand_cv, jd_item["content"])
                ranked_results.append({
                    "jd_id": jd_item["id"],
                    "position_title": jd_item["title"],
                    "department": jd_item.get("department", "General"),
                    "location": jd_item.get("location_type", "Remote"),
                    "match_score": float(match_eval.get("match_score", 50.0)),
                    "summary": match_eval.get("summary", ""),
                    "strengths": match_eval.get("strengths", []),
                    "weaknesses": match_eval.get("weaknesses", []),
                    "jd_content": jd_item["content"]
                })

            ranked_results.sort(key=lambda x: x["match_score"], reverse=True)
            st.session_state.multi_jd_rankings = ranked_results
            st.success(f"Successfully ranked {len(ranked_results)} positions!")

    # ==============================================================================
    # 4. Results Display & Ranking Visualization
    # ==============================================================================
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
            title="Candidate Alignment Across Open Positions",
            text="Match Fit (%)"
        )
        fig_bar.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
        fig_bar.update_layout(yaxis_range=[0, 110])
        st.plotly_chart(fig_bar, use_container_width=True)

        # ==============================================================================
        # 5. Tailored Cover Letter Generator for Selected Position
        # ==============================================================================
        st.markdown("---")
        st.subheader("✉️ Generate Tailored Cover Letter for Selected Position")

        jd_selection_options = {
            f"#{idx} - {r['position_title']} ({r['match_score']}% Match)": r for idx, r in enumerate(rankings, 1)
        }
        chosen_jd_key = st.selectbox(
            "Select Target Position for Cover Letter:",
            list(jd_selection_options.keys())
        )
        selected_record = jd_selection_options[chosen_jd_key]

        c_org, c_cl_gen = st.columns([2, 1])
        with c_org:
            org_name = st.text_input("Target Organization / Company Name", value="Hiring Team")
        with c_cl_gen:
            st.write(" ")
            st.write(" ")
            if st.button("✉️ Synthesize Tailored Cover Letter", type="primary", use_container_width=True):
                with st.spinner(f"Generating personalized cover letter for {selected_record['position_title']}..."):
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
