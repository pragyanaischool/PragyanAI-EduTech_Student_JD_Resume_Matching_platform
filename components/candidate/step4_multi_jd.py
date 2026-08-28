import streamlit as st
import pandas as pd
import plotly.express as px
from database.sql_models import JobDescription
from database.sql_db import sql_db, SessionLocal
from database.chroma_db import chroma
from core.parsers import parse_pdf, parse_docx
from core.pdf_builder import generate_pdf_report
from core.prompt_engine import match_cv_to_jd, generate_cover_letter


def _extract_record_id(record_obj, fallback_val: str) -> str:
    """Safely extracts primary key string regardless of whether record is ORM model, dict, or int."""
    if isinstance(record_obj, dict):
        return str(record_obj.get("id", fallback_val))
    if hasattr(record_obj, "id"):
        return str(getattr(record_obj, "id"))
    if isinstance(record_obj, (int, str)):
        return str(record_obj)
    return str(fallback_val)


def render_step4():
    st.header("Step 4: Multi-JD Match, Ranking & Batch Cover Letter Generation")
    st.caption("Upload multiple JDs, select from indexed database positions, rank position compatibility, and generate tailored cover letters.")

    if not st.session_state.get("cand_cv", "").strip():
        st.warning("⚠️ Please ensure your Master Resume is loaded in Step 1.")
        return

    # Initialize transient evaluation pool
    if "custom_jds_pool" not in st.session_state or not isinstance(st.session_state.custom_jds_pool, list):
        st.session_state.custom_jds_pool = []

    # ==============================================================================
    # 1. Multi-JD Ingestion Hub
    # ==============================================================================
    st.subheader("1. Job Descriptions Selection & Batch Upload Hub")

    tab_upload, tab_db, tab_paste = st.tabs([
        "📁 1. Batch Upload JD Files",
        "🗄️ 2. Select / Extract from Database",
        "📝 3. Quick Paste JDs"
    ])

    # ------------------ TAB 1: BATCH UPLOAD ------------------
    with tab_upload:
        st.markdown("#### Upload Multiple Job Descriptions (PDF / DOCX)")
        uploaded_jd_files = st.file_uploader(
            "Upload one or more JD documents:",
            type=["pdf", "docx"],
            accept_multiple_files=True,
            key="multi_jd_batch_uploader"
        )

        col_up_dept, col_up_loc, col_up_save = st.columns([1, 1, 1])
        with col_up_dept:
            upload_dept = st.text_input("Default Department / Team", value="Engineering", key="up_jd_dept")
        with col_up_loc:
            upload_loc = st.selectbox("Location Type", ["Remote", "Hybrid", "On-site"], key="up_jd_loc")
        with col_up_save:
            save_to_db_toggle = st.checkbox(
                "💾 Save & Index to Database", 
                value=True, 
                help="Automatically save parsed JDs into SQLite & ChromaDB."
            )

        if st.button("📥 Parse & Ingest Uploaded JDs", type="primary", use_container_width=True):
            if uploaded_jd_files:
                successful_count = 0
                for file_index, file_obj in enumerate(uploaded_jd_files):
                    try:
                        file_bytes = file_obj.read()
                        if file_obj.name.lower().endswith(".pdf"):
                            raw_text = parse_pdf(file_bytes)
                        else:
                            raw_text = parse_docx(file_bytes)

                        if raw_text and raw_text.strip():
                            clean_title = file_obj.name.rsplit(".", 1)[0].replace("_", " ").replace("-", " ").title()
                            pool_id = f"batch_{len(st.session_state.custom_jds_pool) + 1}_{file_index}"
                            
                            jd_dict = {
                                "id": pool_id,
                                "title": clean_title,
                                "department": upload_dept,
                                "location_type": upload_loc,
                                "content": raw_text.strip()
                            }
                            st.session_state.custom_jds_pool.append(jd_dict)
                            successful_count += 1

                            # Persist to database
                            if save_to_db_toggle:
                                try:
                                    saved_result = sql_db.save_job_description(
                                        title=clean_title,
                                        department=upload_dept,
                                        location_type=upload_loc,
                                        content=raw_text.strip()
                                    )
                                    db_id = _extract_record_id(saved_result, pool_id)
                                    chroma.upsert_jd(
                                        jd_id=f"jd_{db_id}",
                                        text=raw_text.strip(),
                                        metadata={
                                            "title": clean_title,
                                            "department": upload_dept,
                                            "location_type": upload_loc
                                        }
                                    )
                                except Exception:
                                    pass
                    except Exception as err:
                        st.error(f"Error parsing file '{file_obj.name}': {str(err)}")

                if successful_count > 0:
                    st.success(f"Successfully processed {successful_count} job descriptions!")
                    st.rerun()
                else:
                    st.warning("No readable text found in the uploaded documents.")
            else:
                st.warning("Please upload at least one JD document.")

    # ------------------ TAB 2: DB SELECT ------------------
    with tab_db:
        st.markdown("#### Select and Extract from Existing Database Positions")
        db_records = []
        session = SessionLocal()
        try:
            db_query = session.query(JobDescription).all()
            for jd in db_query:
                db_records.append({
                    "id": f"db_{jd.id}",
                    "db_pk": jd.id,
                    "title": getattr(jd, "title", "Position"),
                    "department": getattr(jd, "department", "Engineering"),
                    "location_type": getattr(jd, "location_type", "Remote"),
                    "content": getattr(jd, "content", "")
                })
        except Exception as e:
            st.error(f"Database query error: {str(e)}")
        finally:
            session.close()

        if db_records:
            db_map = {
                f"#{r['db_pk']} - {r['title']} ({r['department']} | {r['location_type']})": r for r in db_records
            }
            selected_keys = st.multiselect(
                "Select positions to evaluate:",
                options=list(db_map.keys()),
                default=list(db_map.keys())
            )

            if st.button("➕ Add Selected DB JDs to Active Pool", use_container_width=True):
                added_db_count = 0
                for sk in selected_keys:
                    rec = db_map[sk]
                    if not any(x.get("id") == rec["id"] for x in st.session_state.custom_jds_pool):
                        st.session_state.custom_jds_pool.append(rec)
                        added_db_count += 1
                st.success(f"Loaded {added_db_count} positions from database!")
                st.rerun()
        else:
            st.info("No job descriptions found in database. Use Tab 1 to upload and save JDs.")

    # ------------------ TAB 3: QUICK PASTE ------------------
    with tab_paste:
        st.markdown("#### Quick Paste Single Job Description")
        c_p_title, c_p_dept = st.columns(2)
        paste_title = c_p_title.text_input("Job Title", value="Senior AI Systems Engineer", key="quick_paste_title")
        paste_dept = c_p_dept.text_input("Department", value="Engineering", key="quick_paste_dept")
        paste_text = st.text_area("Paste JD Body:", height=150, key="quick_paste_body")
        save_pasted_db = st.checkbox("💾 Save to Database", value=False, key="quick_paste_save_db")

        if st.button("➕ Add Pasted JD to Evaluation Pool", use_container_width=True):
            if paste_text.strip():
                pool_id = f"paste_{len(st.session_state.custom_jds_pool) + 1}"
                entry = {
                    "id": pool_id,
                    "title": paste_title,
                    "department": paste_dept,
                    "location_type": "Remote",
                    "content": paste_text.strip()
                }
                st.session_state.custom_jds_pool.append(entry)

                if save_pasted_db:
                    try:
                        saved_p = sql_db.save_job_description(
                            title=paste_title,
                            department=paste_dept,
                            location_type="Remote",
                            content=paste_text.strip()
                        )
                        db_p_id = _extract_record_id(saved_p, pool_id)
                        chroma.upsert_jd(
                            jd_id=f"jd_{db_p_id}",
                            text=paste_text.strip(),
                            metadata={"title": paste_title, "department": paste_dept, "location_type": "Remote"}
                        )
                    except Exception:
                        pass
                st.success(f"Added '{paste_title}' to pool!")
                st.rerun()
            else:
                st.warning("Please paste JD text.")

    # ==============================================================================
    # 2. Active Evaluation Pool
    # ==============================================================================
    st.markdown("---")
    active_jds = st.session_state.custom_jds_pool

    c_cnt, c_clr = st.columns([3, 1])
    with c_cnt:
        st.subheader(f"2. Active Evaluation Pool ({len(active_jds)} Positions Ready)")
    with c_clr:
        if active_jds and st.button("🗑️ Clear Pool", use_container_width=True):
            st.session_state.custom_jds_pool = []
            st.session_state.multi_jd_rankings = []
            st.rerun()

    if not active_jds:
        st.info("No JDs in the active pool. Upload files in Tab 1, select from DB in Tab 2, or paste in Tab 3.")
        return

    st.write("Loaded Positions: " + " • ".join([f"**{j.get('title', 'Role')}**" for j in active_jds]))

    # ==============================================================================
    # 3. Matching & Ranking Execution
    # ==============================================================================
    if st.button("🚀 Evaluate & Rank Against All Positions in Pool", type="primary", use_container_width=True):
        ranked_list = []
        with st.spinner(f"Matching candidate resume against {len(active_jds)} positions with Groq LLM..."):
            for item in active_jds:
                jd_body = item.get("content", "")
                if jd_body:
                    evaluation = match_cv_to_jd(st.session_state.cand_cv, jd_body)
                    ranked_list.append({
                        "jd_id": item.get("id", "N/A"),
                        "position_title": item.get("title", "Position"),
                        "department": item.get("department", "General"),
                        "location": item.get("location_type", "Remote"),
                        "match_score": float(evaluation.get("match_score", 50.0)),
                        "summary": evaluation.get("summary", ""),
                        "strengths": evaluation.get("strengths", []),
                        "weaknesses": evaluation.get("weaknesses", []),
                        "jd_content": jd_body
                    })

            ranked_list.sort(key=lambda x: x["match_score"], reverse=True)
            st.session_state.multi_jd_rankings = ranked_list
            st.success(f"Ranked {len(ranked_list)} positions successfully!")

    # ==============================================================================
    # 4. Visualization & Rank Display
    # ==============================================================================
    if "multi_jd_rankings" in st.session_state and st.session_state.multi_jd_rankings:
        rankings = st.session_state.multi_jd_rankings
        st.markdown("---")
        st.subheader("🏆 Ranked Compatibility Matrix")

        df_rank = pd.DataFrame([{
            "Rank": f"#{i}",
            "Position": r["position_title"],
            "Department": r["department"],
            "Location": r["location"],
            "Match Fit (%)": r["match_score"]
        } for i, r in enumerate(rankings, 1)])

        st.dataframe(df_rank, use_container_width=True)

        fig_bar = px.bar(
            df_rank,
            x="Position",
            y="Match Fit (%)",
            color="Match Fit (%)",
            color_continuous_scale="Blues",
            title="Candidate Alignment Across Uploaded JDs",
            text="Match Fit (%)"
        )
        fig_bar.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
        fig_bar.update_layout(yaxis_range=[0, 115])
        st.plotly_chart(fig_bar, use_container_width=True)

        # ==============================================================================
        # 5. Tailored Cover Letter Generator
        # ==============================================================================
        st.markdown("---")
        st.subheader("✉️ Generate Tailored Cover Letter for Selected Position")

        position_selector_map = {
            f"#{i} - {r['position_title']} ({r['match_score']}% Match)": r for i, r in enumerate(rankings, 1)
        }
        chosen_key = st.selectbox("Select Target Position:", list(position_selector_map.keys()))
        selected_target = position_selector_map[chosen_key]

        c_org, c_cl_btn = st.columns([2, 1])
        with c_org:
            org_name = st.text_input("Target Organization Name", value="Hiring Team")
        with c_cl_btn:
            st.write(" ")
            st.write(" ")
            if st.button("✉️ Synthesize Cover Letter", type="primary", use_container_width=True):
                with st.spinner(f"Writing customized cover letter for {selected_target['position_title']}..."):
                    letter_text = generate_cover_letter(
                        st.session_state.cand_cv,
                        selected_target["jd_content"],
                        company_name=org_name
                    )
                    st.session_state.active_cover_letter = letter_text
                    st.success("Cover letter synthesized!")

        if "active_cover_letter" in st.session_state and st.session_state.active_cover_letter:
            st.session_state.active_cover_letter = st.text_area(
                "Generated Cover Letter",
                value=st.session_state.active_cover_letter,
                height=260
            )
            cl_pdf = generate_pdf_report(st.session_state.active_cover_letter, title=f"Cover Letter - {org_name}")
            st.download_button(
                label="📥 Download Cover Letter PDF",
                data=cl_pdf,
                file_name=f"Cover_Letter_{selected_target['position_title'].replace(' ', '_')}.pdf",
                mime="application/pdf",
                type="primary"
            )
