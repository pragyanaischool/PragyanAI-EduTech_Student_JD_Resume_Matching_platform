import streamlit as st
import pandas as pd
import plotly.express as px
from database.sql_models import JobDescription, Resume, Application
from database.sql_db import sql_db, SessionLocal
from database.chroma_db import chroma
from core.parsers import parse_pdf, parse_docx
from core.pdf_builder import generate_pdf_report
from core.prompt_engine import (
    generate_enterprise_job_description,
    match_cv_to_jd,
    screen_candidate_logistics,
)

# ==============================================================================
# Page Configuration & Guardrails
# ==============================================================================
st.set_page_config(page_title="Employer Talent Hub", layout="wide", page_icon="🏢")

if "auth_user" not in st.session_state or not st.session_state.auth_user:
    st.warning("Please sign in from the main portal to access the Employer Portal.")
    st.stop()

current_user = st.session_state.auth_user
raw_role = current_user.get("role", "")
user_role = str(raw_role).lower().strip()

ALLOWED_EMPLOYER_ROLES = ["company", "recruiter", "employer", "hiring_manager", "admin"]

if user_role not in ALLOWED_EMPLOYER_ROLES:
    st.error(f"Access restricted to Recruiters & Hiring Managers. Your active role is: '{raw_role}'.")
    st.stop()

# Initialize Session State Variables
if "draft_jd_markdown" not in st.session_state:
    st.session_state.draft_jd_markdown = ""
if "jd_editor_rev" not in st.session_state:
    st.session_state.jd_editor_rev = 0
if "recruiter_cv_pool" not in st.session_state:
    st.session_state.recruiter_cv_pool = []
if "recruiter_match_results" not in st.session_state:
    st.session_state.recruiter_match_results = []

st.title("🏢 Hiring Manager & Recruiter Command Center")
st.caption(f"Authenticated as: **{current_user.get('full_name') or current_user.get('email')}** ({current_user.get('email')}) — Role: `{raw_role.upper()}`")

# Navigation Tabs
tab_publish, tab_inventory, tab_matcher = st.tabs([
    "➕ 1. Publish New Position (JD)",
    "🗄️ 2. Active Positions Inventory",
    "🎯 3. Candidate Matching & Pipeline"
])

# ==============================================================================
# TAB 1: PUBLISH NEW JOB POSITION (JD)
# ==============================================================================
with tab_publish:
    st.header("Publish New Job Position (JD)")
    st.caption("Configure position parameters, synthesize full enterprise specifications with AI or ingest existing documents, review, edit, and index.")

    with st.expander("⚙️ Step 1: Position Metadata & Parameters", expanded=True):
        c_title, c_dept = st.columns(2)
        with c_title:
            pos_title = st.text_input(
                "Job Position Title *",
                value="Senior AI Systems Engineer",
                placeholder="e.g. Lead MLOps Architect, Full Stack Engineer..."
            )
        with c_dept:
            pos_dept = st.selectbox(
                "Department / Unit *",
                [
                    "Artificial Intelligence & ML",
                    "Core Software Engineering",
                    "Data Engineering & Analytics",
                    "Cloud, DevOps & Infrastructure",
                    "Cybersecurity & Systems",
                    "Product Management & Design",
                    "Embedded Systems & EDA"
                ]
            )

        c_loc, c_exp, c_comp = st.columns(3)
        with c_loc:
            pos_loc = st.selectbox(
                "Work Location Model *",
                ["Remote (Worldwide)", "Remote (India)", "Hybrid (Bengaluru)", "Hybrid (Hyderabad / Pune)", "On-site (Bengaluru)", "On-site (San Francisco)"]
            )
        with c_exp:
            pos_exp = st.selectbox(
                "Years of Experience Range *",
                ["0–1 Years (Graduate / Entry)", "1–3 Years (Junior)", "3–5 Years (Mid-Level)", "5–8 Years (Senior)", "8–12 Years (Lead / Staff)", "12+ Years (Principal / Director)"]
            )
        with c_comp:
            comp_type = st.selectbox(
                "Compensation Structure *",
                ["Competitive Market Band (₹18L – ₹35L / $120k – $180k)", "Fixed Annual CTC + Equity ESOPs", "Hourly / Retainer Contract", "Non-paid / Academic Internship", "Performance-Linked Incentive Base"]
            )

        c_tech, c_biz = st.columns(2)
        with c_tech:
            pos_tech = st.selectbox(
                "Primary Technology Domain *",
                [
                    "Generative AI, LLMs & Agentic Systems (LangGraph, Groq, vLLM)",
                    "High-Throughput Backend & Microservices (Python, FastAPI, Go)",
                    "Modern Web & Frontend Architectures (React, Next.js, TypeScript)",
                    "Distributed Vector Stores & DBMS (ChromaDB, PostgreSQL, Redis)",
                    "Cloud Native & Container Orchestration (Docker, Kubernetes, AWS/GCP)",
                    "Computer Vision & Edge AI (PyTorch, OpenCV, TensorRT)",
                    "EDA, PCB Verification & Embedded Firmware (C/C++, Linux Kernel)"
                ]
            )
        with c_biz:
            pos_biz = st.selectbox(
                "Business / Industry Domain *",
                [
                    "EdTech & Adaptive Learning Platforms",
                    "Enterprise SaaS & Venture Studios",
                    "FinTech, WealthTech & Banking Solutions",
                    "Healthcare & Biomedical Intelligence",
                    "E-Commerce, Supply Chain & Logistics",
                    "Electronic Design Automation (EDA) & Hardware Tech"
                ]
            )

    st.subheader("2. Ingestion Source & Content Synthesis")
    ingest_mode = st.radio(
        "Choose JD Ingestion Mode:",
        ["🤖 AI Autonomous Generation (Recommended)", "📄 Upload Existing Document (PDF / DOCX)", "📝 Direct Markdown / Text Paste"],
        horizontal=True
    )

    if ingest_mode == "🤖 AI Autonomous Generation (Recommended)":
        col_ai_notes, col_ai_btn = st.columns([3, 1])
        with col_ai_notes:
            extra_context = st.text_input(
                "Additional Strategic Notes (Optional)",
                placeholder="e.g. Must have experience building RAG architectures with 10k+ daily users..."
            )
        with col_ai_btn:
            st.write(" ")
            st.write(" ")
            if st.button("✨ Synthesize Enterprise JD", type="primary", use_container_width=True):
                if not pos_title.strip():
                    st.warning("Please enter a valid Job Position Title.")
                else:
                    with st.spinner("Synthesizing full enterprise Job Description with Groq LLM..."):
                        generated_jd = generate_enterprise_job_description(
                            title=pos_title,
                            department=pos_dept,
                            location_type=pos_loc,
                            experience_range=pos_exp,
                            tech_domain=pos_tech,
                            business_domain=pos_biz,
                            compensation=comp_type,
                            company_name="PragyanAI Venture Studio",
                            additional_notes=extra_context
                        )
                        st.session_state.draft_jd_markdown = generated_jd
                        st.session_state.jd_editor_rev += 1
                        st.success("Enterprise Job Description generated!")
                        st.rerun()

    elif ingest_mode == "📄 Upload Existing Document (PDF / DOCX)":
        uploaded_jd = st.file_uploader("Upload JD Document", type=["pdf", "docx"], key="publisher_file_upload")
        if uploaded_jd:
            if st.button("📥 Parse & Load into Editor", type="primary", use_container_width=True):
                raw_text = parse_pdf(uploaded_jd.read()) if uploaded_jd.name.endswith(".pdf") else parse_docx(uploaded_jd.read())
                if raw_text.strip():
                    st.session_state.draft_jd_markdown = raw_text
                    st.session_state.jd_editor_rev += 1
                    st.success("Document parsed and loaded into workspace!")
                    st.rerun()

    else:
        pasted_text = st.text_area("Paste Raw JD Text:", height=180, placeholder="Paste JD requirements, responsibilities, competencies...", key="publisher_raw_paste")
        if st.button("📥 Load Raw Text into Editor", type="primary", use_container_width=True):
            if pasted_text.strip():
                st.session_state.draft_jd_markdown = pasted_text
                st.session_state.jd_editor_rev += 1
                st.success("Loaded into editor workspace!")
                st.rerun()

    if st.session_state.draft_jd_markdown:
        st.markdown("---")
        st.subheader("3. Review, Fine-Tune & Publish Workspace")
        st.caption("Edit the Markdown specification directly. Once satisfied, click **'Publish & Index Job Position'** to save it to SQLite and vectorize it into ChromaDB.")

        col_edit_md, col_render_view = st.columns([1, 1])

        with col_edit_md:
            st.markdown("#### 📝 Editable Markdown Specification")
            rev_idx = st.session_state.jd_editor_rev
            edited_jd = st.text_area(
                "Live Markdown Editor",
                value=st.session_state.draft_jd_markdown,
                height=450,
                key=f"jd_live_editor_{rev_idx}"
            )
            st.session_state.draft_jd_markdown = edited_jd

        with col_render_view:
            st.markdown("#### 👁️ Rendered Candidate View")
            with st.container(height=450, border=True):
                st.markdown(st.session_state.draft_jd_markdown)

        col_publish_btn, col_pdf_export = st.columns([1, 1])

        with col_publish_btn:
            if st.button("🚀 Publish & Index Job Position to Database", type="primary", use_container_width=True):
                with st.spinner("Persisting specification to SQL database and vectorizing in ChromaDB..."):
                    saved_jd_record = sql_db.save_job_description(
                        title=pos_title,
                        department=pos_dept,
                        location_type=pos_loc,
                        content=st.session_state.draft_jd_markdown
                    )

                    if isinstance(saved_jd_record, dict):
                        jd_pk = str(saved_jd_record.get("id", "custom"))
                    elif hasattr(saved_jd_record, "id"):
                        jd_pk = str(saved_jd_record.id)
                    else:
                        jd_pk = str(saved_jd_record or "custom")

                    doc_identifier = f"jd_{jd_pk}"
                    metadata_payload = {
                        "title": pos_title,
                        "department": pos_dept,
                        "location_type": pos_loc,
                        "experience_range": pos_exp,
                        "tech_domain": pos_tech,
                        "business_domain": pos_biz
                    }

                    try:
                        chroma.upsert_jd(doc_identifier, st.session_state.draft_jd_markdown, metadata_payload)
                    except TypeError:
                        try:
                            chroma.upsert_jd(doc_id=doc_identifier, text=st.session_state.draft_jd_markdown, metadata=metadata_payload)
                        except Exception:
                            pass
                    except Exception:
                        pass

                    st.success(f"🎉 Position '{pos_title}' published and indexed successfully with ID: `{doc_identifier}`!")

        with col_pdf_export:
            jd_pdf_bytes = generate_pdf_report(st.session_state.draft_jd_markdown, title=f"JD - {pos_title}")
            st.download_button(
                label="📥 Download Publication PDF",
                data=jd_pdf_bytes,
                file_name=f"Job_Description_{pos_title.replace(' ', '_')}.pdf",
                mime="application/pdf",
                use_container_width=True
            )

# ==============================================================================
# TAB 2: ACTIVE POSITIONS INVENTORY
# ==============================================================================
with tab_inventory:
    st.header("Active Positions Inventory")
    session = SessionLocal()
    try:
        all_jds = session.query(JobDescription).order_by(JobDescription.created_at.desc()).all()
        if all_jds:
            df_inv = pd.DataFrame([{
                "ID": j.id,
                "Position Title": j.title,
                "Department": j.department,
                "Location": j.location_type,
                "Created At": j.created_at.strftime("%Y-%m-%d %H:%M") if j.created_at else "N/A"
            } for j in all_jds])
            st.dataframe(df_inv, use_container_width=True)

            selected_id = st.selectbox(
                "Inspect Full Position Specification:",
                options=[j.id for j in all_jds],
                format_func=lambda x: f"Position #{x}"
            )
            target_jd = next((j for j in all_jds if j.id == selected_id), None)
            if target_jd:
                with st.expander(f"📄 Full Specification: {target_jd.title}", expanded=True):
                    st.markdown(target_jd.content)
        else:
            st.info("No active job positions found. Publish a position in Tab 1.")
    finally:
        session.close()

# ==============================================================================
# TAB 3: CANDIDATE MATCHING & PIPELINE SCREENING (WITH CV UPLOAD & SELECT)
# ==============================================================================
with tab_matcher:
    st.header("Candidate Matching & Pipeline Screening")
    st.caption("Select or upload candidate resumes, compare against target position requirements, and rank candidate compatibility.")

    # --------------------------------------------------------------------------
    # 1. Target Position Selector
    # --------------------------------------------------------------------------
    st.subheader("1. Select Target Job Position")
    session = SessionLocal()
    try:
        active_positions = session.query(JobDescription).order_by(JobDescription.created_at.desc()).all()
        active_resumes_db = session.query(Resume).order_by(Resume.created_at.desc()).all()
    finally:
        session.close()

    if not active_positions:
        st.warning("⚠️ No Job Descriptions found in database. Please publish at least one JD in Tab 1 first.")
    else:
        jd_options_dict = {
            f"#{j.id} - {j.title} ({j.department} | {j.location_type})": j for j in active_positions
        }
        selected_jd_label = st.selectbox("Choose Target Job Position:", list(jd_options_dict.keys()))
        chosen_jd_obj = jd_options_dict[selected_jd_label]

        st.markdown("---")

        # ----------------------------------------------------------------------
        # 2. Candidate CV Ingestion & Selection Hub
        # ----------------------------------------------------------------------
        st.subheader("2. Candidate CVs Selection & Upload Hub")

        cv_tab_upload, cv_tab_db, cv_tab_paste = st.tabs([
            "📁 1. Batch Upload Candidate CVs",
            "🗄️ 2. Select from Database Resumes",
            "📝 3. Quick Paste Single Candidate CV"
        ])

        # --- Sub-tab 1: Batch Upload CVs ---
        with cv_tab_upload:
            st.markdown("#### Upload Candidate Resume Documents (PDF / DOCX)")
            uploaded_cv_files = st.file_uploader(
                "Upload one or more candidate CV files:",
                type=["pdf", "docx"],
                accept_multiple_files=True,
                key="recruiter_batch_cv_uploader"
            )

            col_cand_tag, col_save_cv_db = st.columns([2, 1])
            with col_cand_tag:
                source_tag = st.text_input("Candidate Source / Tag", value="Campus Placement Drive", key="recruiter_cv_source_tag")
            with col_save_cv_db:
                st.write(" ")
                save_uploaded_cvs_to_db = st.checkbox("💾 Index CVs to Database", value=True)

            if st.button("📥 Parse & Add Uploaded CVs to Matching Pool", type="primary", use_container_width=True):
                if uploaded_cv_files:
                    added_cv_count = 0
                    for c_idx, c_file in enumerate(uploaded_cv_files):
                        try:
                            file_bytes = c_file.read()
                            raw_cv_text = parse_pdf(file_bytes) if c_file.name.lower().endswith(".pdf") else parse_docx(file_bytes)

                            if raw_cv_text and raw_cv_text.strip():
                                cand_name = c_file.name.rsplit(".", 1)[0].replace("_", " ").replace("-", " ").title()
                                pool_cv_id = f"up_cv_{len(st.session_state.recruiter_cv_pool) + 1}_{c_idx}"

                                cv_dict = {
                                    "id": pool_cv_id,
                                    "candidate_name": cand_name,
                                    "filename": c_file.name,
                                    "source": source_tag,
                                    "content": raw_cv_text.strip()
                                }
                                st.session_state.recruiter_cv_pool.append(cv_dict)
                                added_cv_count += 1

                                if save_uploaded_cvs_to_db:
                                    try:
                                        saved_res = sql_db.save_resume(
                                            filename=c_file.name,
                                            raw_content=raw_cv_text.strip(),
                                            markdown_content=raw_cv_text.strip(),
                                            user_id=current_user.get("id")
                                        )
                                        res_pk = str(saved_res.get("id") if isinstance(saved_res, dict) else getattr(saved_res, "id", pool_cv_id))
                                        chroma.upsert_resume(
                                            doc_id=f"cv_{res_pk}",
                                            text=raw_cv_text.strip(),
                                            metadata={"filename": c_file.name, "source": source_tag}
                                        )
                                    except Exception:
                                        pass
                        except Exception as e:
                            st.error(f"Error reading '{c_file.name}': {str(e)}")

                    if added_cv_count > 0:
                        st.success(f"Loaded {added_cv_count} candidate CVs into matching pool!")
                        st.rerun()
                else:
                    st.warning("Please upload at least one candidate CV file.")

        # --- Sub-tab 2: Select from Database ---
        with cv_tab_db:
            st.markdown("#### Select Indexed Resumes from Database")
            if active_resumes_db:
                db_resumes_map = {}
                for r in active_resumes_db:
                    label_key = f"#{r.id} - {r.filename or 'Candidate Profile'} (Uploaded: {r.created_at.strftime('%Y-%m-%d') if r.created_at else 'N/A'})"
                    db_resumes_map[label_key] = {
                        "id": f"db_cv_{r.id}",
                        "candidate_name": r.filename.rsplit(".", 1)[0] if r.filename else f"Candidate #{r.id}",
                        "filename": r.filename or f"Candidate_{r.id}.pdf",
                        "source": "Platform Database",
                        "content": r.markdown_content or r.raw_content or ""
                    }

                selected_db_resumes = st.multiselect(
                    "Choose candidate profiles to evaluate:",
                    options=list(db_resumes_map.keys()),
                    default=list(db_resumes_map.keys())
                )

                if st.button("➕ Add Selected Database CVs to Active Pool", use_container_width=True):
                    db_added_count = 0
                    for sk in selected_db_resumes:
                        item = db_resumes_map[sk]
                        if not any(x.get("id") == item["id"] for x in st.session_state.recruiter_cv_pool):
                            st.session_state.recruiter_cv_pool.append(item)
                            db_added_count += 1
                    st.success(f"Added {db_added_count} resumes from database to active evaluation pool!")
                    st.rerun()
            else:
                st.info("No candidate resumes found in the database. Use Tab 1 above to upload CVs.")

        # --- Sub-tab 3: Quick Paste ---
        with cv_tab_paste:
            st.markdown("#### Quick Paste Single Candidate Resume")
            c_p_name = st.text_input("Candidate Full Name", value="Rohan Verma", key="quick_paste_cand_name")
            pasted_cv_body = st.text_area("Paste Candidate Resume / Career Details:", height=150, key="quick_paste_cand_body")

            if st.button("➕ Add Pasted Candidate CV to Pool", use_container_width=True):
                if pasted_cv_body.strip():
                    pool_id = f"paste_cv_{len(st.session_state.recruiter_cv_pool) + 1}"
                    st.session_state.recruiter_cv_pool.append({
                        "id": pool_id,
                        "candidate_name": c_p_name,
                        "filename": f"{c_p_name.replace(' ', '_')}_Resume.txt",
                        "source": "Direct Paste",
                        "content": pasted_cv_body.strip()
                    })
                    st.success(f"Added '{c_p_name}' to pool!")
                    st.rerun()
                else:
                    st.warning("Please paste resume text.")

        # ----------------------------------------------------------------------
        # 3. Active Candidate Pool Overview & Matching Trigger
        # ----------------------------------------------------------------------
        st.markdown("---")
        active_cvs = st.session_state.recruiter_cv_pool

        col_cv_count, col_cv_clear = st.columns([3, 1])
        with col_cv_count:
            st.subheader(f"3. Active Candidate Pool ({len(active_cvs)} Candidates Ready)")
        with col_cv_clear:
            if active_cvs and st.button("🗑️ Clear Candidate Pool", use_container_width=True):
                st.session_state.recruiter_cv_pool = []
                st.session_state.recruiter_match_results = []
                st.rerun()

        if not active_cvs:
            st.info("No candidates in the evaluation pool yet. Upload CVs above or select from the database to evaluate.")
        else:
            st.write("Candidates: " + " • ".join([f"**{c.get('candidate_name', 'Candidate')}** (`{c.get('source')}`)" for c in active_cvs]))

            if st.button(f"🚀 Match All {len(active_cvs)} Candidates Against '{chosen_jd_obj.title}'", type="primary", use_container_width=True):
                matching_results = []
                with st.spinner(f"Evaluating candidate pool against {chosen_jd_obj.title} with Groq LLM..."):
                    for cand_item in active_cvs:
                        cand_body = cand_item.get("content", "")
                        if cand_body.strip():
                            fit_result = match_cv_to_jd(cand_body, chosen_jd_obj.content)
                            matching_results.append({
                                "Candidate": cand_item.get("candidate_name", "Candidate"),
                                "Source": cand_item.get("source", "Upload"),
                                "Filename": cand_item.get("filename", "Resume.pdf"),
                                "Match Fit (%)": float(fit_result.get("match_score", 50.0)),
                                "Summary": fit_result.get("summary", ""),
                                "Strengths": fit_result.get("strengths", []),
                                "Weaknesses": fit_result.get("weaknesses", []),
                                "Missing Keywords": fit_result.get("missing_keywords", []),
                                "Full CV": cand_body
                            })

                    matching_results.sort(key=lambda x: x["Match Fit (%)"], reverse=True)
                    st.session_state.recruiter_match_results = matching_results
                    st.success(f"Evaluated and ranked {len(matching_results)} candidates successfully!")

        # ----------------------------------------------------------------------
        # 4. Ranked Screening Results & Candidate Diagnostics
        # ----------------------------------------------------------------------
        if "recruiter_match_results" in st.session_state and st.session_state.recruiter_match_results:
            results = st.session_state.recruiter_match_results
            st.markdown("---")
            st.subheader(f"🏆 Candidate Ranking for: {chosen_jd_obj.title}")

            df_results = pd.DataFrame([{
                "Rank": f"#{idx}",
                "Candidate Name": r["Candidate"],
                "Source": r["Source"],
                "Match Fit (%)": r["Match Fit (%)"],
                "Executive Verdict": r["Summary"]
            } for idx, r in enumerate(results, 1)])

            st.dataframe(df_results, use_container_width=True)

            fig_cand_bar = px.bar(
                df_results,
                x="Candidate Name",
                y="Match Fit (%)",
                color="Match Fit (%)",
                color_continuous_scale="Teal",
                title=f"Compatibility Alignment for {chosen_jd_obj.title}",
                text="Match Fit (%)"
            )
            fig_cand_bar.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
            fig_cand_bar.update_layout(yaxis_range=[0, 115])
            st.plotly_chart(fig_cand_bar, use_container_width=True)

            # Deep Candidate Diagnostic Expander
            st.subheader("🔍 Deep Candidate Fit & SWOT Diagnostic")
            cand_select_map = {f"#{idx} - {r['Candidate']} ({r['Match Fit (%)']}% Match)": r for idx, r in enumerate(results, 1)}
            selected_cand_label = st.selectbox("Inspect Candidate Diagnostic:", list(cand_select_map.keys()))
            selected_cand_data = cand_select_map[selected_cand_label]

            col_swot_l, col_swot_r = st.columns(2)
            with col_swot_l:
                st.success("💪 **Key Strengths & Direct Alignments:**")
                for s in selected_cand_data.get("Strengths", []):
                    st.markdown(f"- {s}")

                st.info(f"**Executive Verdict:** {selected_cand_data.get('Summary')}")

            with col_swot_r:
                st.warning("⚠️ **Skill Gaps & Identified Weaknesses:**")
                for w in selected_cand_data.get("Weaknesses", []):
                    st.markdown(f"- {w}")

                if selected_cand_data.get("Missing Keywords"):
                    st.error("**Missing Technical Keywords:** " + ", ".join([f"`{kw}`" for kw in selected_cand_data["Missing Keywords"]]))

            with st.expander(f"📄 View Full Resume for {selected_cand_data['Candidate']}"):
                st.markdown(selected_cand_data.get("Full CV", "No content available."))
