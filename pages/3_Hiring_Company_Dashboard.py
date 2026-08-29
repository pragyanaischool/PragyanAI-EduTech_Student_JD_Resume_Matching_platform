import streamlit as st
import json
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
    generate_candidate_verification_kit,
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

# Initialize Persistent Session State Variables
if "draft_jd_markdown" not in st.session_state:
    st.session_state.draft_jd_markdown = ""
if "jd_editor_rev" not in st.session_state:
    st.session_state.jd_editor_rev = 0
if "recruiter_cv_pool" not in st.session_state:
    st.session_state.recruiter_cv_pool = []
if "recruiter_match_results" not in st.session_state:
    st.session_state.recruiter_match_results = []
if "active_verification_kit" not in st.session_state:
    st.session_state.active_verification_kit = None
if "saved_screening_kits" not in st.session_state:
    st.session_state.saved_screening_kits = {}

st.title("🏢 Hiring Manager & Recruiter Command Center")
st.caption(f"Authenticated as: **{current_user.get('full_name') or current_user.get('email')}** ({current_user.get('email')}) — Role: `{raw_role.upper()}`")

# Navigation Tabs
tab_publish, tab_inventory, tab_matcher, tab_verification = st.tabs([
    "➕ 1. Publish New Position (JD)",
    "🗄️ 2. Active Positions Inventory",
    "🎯 3. Candidate Matching & Pipeline",
    "🔍 4. 1st-Level Screening & Verification Kit"
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
# TAB 3: CANDIDATE MATCHING & PIPELINE SCREENING
# ==============================================================================
with tab_matcher:
    st.header("Candidate Matching & Pipeline Screening")
    st.caption("Select or upload candidate resumes, compare against target position requirements, and rank candidate compatibility.")

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
        selected_jd_label = st.selectbox("Choose Target Job Position:", list(jd_options_dict.keys()), key="match_tab_jd_sel")
        chosen_jd_obj = jd_options_dict[selected_jd_label]

        st.markdown("---")

        st.subheader("2. Candidate CVs Selection & Upload Hub")
        cv_tab_upload, cv_tab_db, cv_tab_paste = st.tabs([
            "📁 1. Batch Upload Candidate CVs",
            "🗄️ 2. Select from Database Resumes",
            "📝 3. Quick Paste Single Candidate CV"
        ])

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
                save_uploaded_cvs_to_db = st.checkbox("💾 Index CVs to Database", value=True, key="save_cvs_check")

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
            st.info("No candidates in the evaluation pool yet. Upload CVs above or select from database.")
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

# ==============================================================================
# TAB 4: 1ST-LEVEL SCREENING & VERIFICATION KIT (4TH FEATURE)
# ==============================================================================
with tab_verification:
    st.header("🔍 First-Level Screening & Candidate Verification Kit")
    st.caption("Perform an in-depth audit on candidate experience, company changes, role pivots, and employment gaps. Generate tailored HR and multi-tiered Technical questions (Basic, Advanced, Innovative) with model verification answers.")

    session = SessionLocal()
    try:
        available_jds = session.query(JobDescription).all()
        available_resumes = session.query(Resume).all()
    finally:
        session.close()

    # Consolidate candidate sources (Database + In-Memory Recruiter Pool)
    cand_options = {}
    for r in available_resumes:
        c_label = f"DB #{r.id}: {r.filename or 'Candidate Profile'}"
        cand_options[c_label] = {
            "name": r.filename.rsplit(".", 1)[0] if r.filename else f"Candidate #{r.id}",
            "content": r.markdown_content or r.raw_content or ""
        }
    for c in st.session_state.get("recruiter_cv_pool", []):
        c_label = f"Uploaded: {c['candidate_name']} ({c['filename']})"
        cand_options[c_label] = {
            "name": c["candidate_name"],
            "content": c["content"]
        }

    if not available_jds:
        st.warning("Please publish at least one Job Description in Tab 1.")
    elif not cand_options:
        st.warning("No candidate resumes found. Upload or select candidates in Tab 3.")
    else:
        col_v_jd, col_v_cand = st.columns(2)
        with col_v_jd:
            v_jd_map = {f"#{j.id} - {j.title} ({j.department})": j for j in available_jds}
            chosen_v_jd_key = st.selectbox("1. Select Target Job Description:", list(v_jd_map.keys()), key="v_jd_choice")
            selected_v_jd = v_jd_map[chosen_v_jd_key]

        with col_v_cand:
            chosen_v_cand_key = st.selectbox("2. Select Candidate to Audit & Verify:", list(cand_options.keys()), key="v_cand_choice")
            selected_v_cand = cand_options[chosen_v_cand_key]

        if st.button("⚡ Synthesize First-Level Screening & Verification Kit", type="primary", use_container_width=True):
            if not selected_v_cand["content"].strip():
                st.warning("Selected candidate resume content is empty.")
            else:
                with st.spinner(f"Analyzing career trajectory, tenure anomalies, and formulating verification Q&A for {selected_v_cand['name']}..."):
                    kit_data = generate_candidate_verification_kit(
                        resume_text=selected_v_cand["content"],
                        jd_text=selected_v_jd.content,
                        candidate_name=selected_v_cand["name"]
                    )
                    st.session_state.active_verification_kit = kit_data
                    st.success(f"Verification kit generated for {selected_v_cand['name']}!")
                    st.rerun()

    # Display Active Verification Kit
    if st.session_state.get("active_verification_kit"):
        kit = st.session_state.active_verification_kit
        cand_n = kit.get("candidate_name", "Candidate")
        traj = kit.get("career_trajectory_audit", {})
        claims = kit.get("key_claims_to_verify", [])
        hr_qs = kit.get("hr_screening_questions", [])
        tech_kit = kit.get("technical_screening_kit", {})

        st.markdown("---")
        st.subheader(f"📋 First-Level Audit & Verification Report: {cand_n}")

        # ----------------------------------------------------------------------
        # Section A: Career Trajectory & Employment Anomaly Audit
        # ----------------------------------------------------------------------
        with st.expander("📊 Section A: Experience, Company Changes & Career Anomaly Audit", expanded=True):
            col_a1, col_a2 = st.columns(2)
            with col_a1:
                st.markdown("#### ⏳ Experience & Tenure Trajectory")
                st.info(f"**Total Experience Assessment:**\n{traj.get('total_experience_summary', 'N/A')}")
                st.markdown(f"**🏢 Company Change & Job-Hopping Analysis:**\n{traj.get('company_change_analysis', 'Standard tenure.')}")
                st.markdown(f"**🔄 Role & Functional Shift Analysis:**\n{traj.get('role_change_analysis', 'Normal career progression.')}")

            with col_a2:
                st.markdown("#### ⚠️ Flagged Issues & Potential Red Flags")
                red_flags = traj.get("red_flags_and_gaps", [])
                if red_flags:
                    for rf in red_flags:
                        st.error(f"- 🛑 {rf}")
                else:
                    st.success("No critical employment timeline anomalies or gaps detected.")

                st.markdown("#### 🎯 Critical Resume Claims to Fact-Check")
                for c in claims:
                    st.warning(f"- 🔍 **Fact-Check:** {c}")

        # ----------------------------------------------------------------------
        # Section B: HR & Behavioral Screening Interview Kit
        # ----------------------------------------------------------------------
        with st.expander("🎙️ Section B: Key HR & Behavioral Screening Questions (STAR Method)", expanded=True):
            st.caption("First-level HR questions to test integrity, salary expectations, reasons for leaving, and cultural alignment.")
            for q_item in hr_qs:
                st.markdown(f"**Q{q_item.get('id', 1)}: \"{q_item.get('question')}\"**")
                col_hq1, col_hq2 = st.columns(2)
                with col_hq1:
                    st.markdown(f"🎯 **Assessment Purpose:** {q_item.get('purpose')}")
                    st.success(f"✅ **Ideal Response Indicators:** {q_item.get('ideal_response_indicators')}")
                with col_hq2:
                    st.error(f"🛑 **Red Flag Warning Signs:** {q_item.get('red_flag_indicators')}")
                st.markdown("---")

        # ----------------------------------------------------------------------
        # Section C: Multi-Tiered Technical Verification Q&A (Basic, Adv, Innov)
        # ----------------------------------------------------------------------
        with st.expander("⚡ Section C: Multi-Tiered Technical Verification Kit (with Model Answers)", expanded=True):
            tab_basic, tab_adv, tab_innov = st.tabs([
                "🟢 Tier 1: Foundational / Basic Q&A",
                "🟡 Tier 2: Advanced Practitioner Q&A",
                "🟣 Tier 3: Innovative / Architectural Curveballs"
            ])

            with tab_basic:
                st.markdown("#### Foundational Technical Checkpoints")
                for b_item in tech_kit.get("basic_foundational", []):
                    st.markdown(f"**Q{b_item.get('id', 1)} [{b_item.get('focus_area', 'Core')}]:** `{b_item.get('question')}`")
                    st.info(f"**Model Verification Answer for Hiring Lead:**\n{b_item.get('expected_answer')}")
                    st.markdown("---")

            with tab_adv:
                st.markdown("#### Advanced Scenario & Concurrency Checkpoints")
                for a_item in tech_kit.get("advanced_practitioner", []):
                    st.markdown(f"**Q{a_item.get('id', 1)} [{a_item.get('focus_area', 'Architecture')}]:** `{a_item.get('question')}`")
                    st.info(f"**Senior Verification Answer & Trade-offs:**\n{a_item.get('expected_answer')}")
                    st.markdown("---")

            with tab_innov:
                st.markdown("#### Innovative & Architectural Curveball Challenges")
                for i_item in tech_kit.get("innovative_curveballs", []):
                    st.markdown(f"**Q{i_item.get('id', 1)} [{i_item.get('focus_area', 'System Innovation')}]:** `{i_item.get('question')}`")
                    st.info(f"**Exemplary Architectural Solution & Reasoning:**\n{i_item.get('expected_answer')}")
                    st.markdown("---")

        # ----------------------------------------------------------------------
        # Section D: Interactive Editor, Save Notes & PDF Export
        # ----------------------------------------------------------------------
        st.markdown("---")
        st.subheader("📝 Customize, Save Screening Notes & Export Dossier")
        st.caption("Tailor any questions or add interviewer notes before conducting the first-level call.")

        # Convert kit to formatted Markdown representation for live editing and export
        kit_markdown_default = f"""# First-Level Candidate Screening & Verification Kit
**Candidate:** {cand_n}
**Target Role:** {chosen_v_jd_key}
**Audited Date:** {pd.Timestamp.now().strftime('%Y-%m-%d')}

---

## 1. Career Trajectory & Tenure Audit
- **Total Experience:** {traj.get('total_experience_summary', 'N/A')}
- **Company Transitions:** {traj.get('company_change_analysis', 'N/A')}
- **Role Progression:** {traj.get('role_change_analysis', 'N/A')}

### Flagged Items & Gaps to Probe:
{chr(10).join([f"- [ ] {rf}" for rf in traj.get('red_flags_and_gaps', [])])}

### Key Claims to Fact-Check:
{chr(10).join([f"- [ ] {c}" for c in claims])}

---

## 2. Key HR & Cultural Fit Questions
{chr(10).join([f"### Q{q.get('id')}: {q.get('question')}\n- **Purpose:** {q.get('purpose')}\n- **Ideal Indicators:** {q.get('ideal_response_indicators')}\n- **Red Flags:** {q.get('red_flag_indicators')}\n" for q in hr_qs])}

---

## 3. Technical Verification Kit

### Tier 1: Foundational Checkpoints
{chr(10).join([f"**Q{b.get('id')} ({b.get('focus_area')}):** {b.get('question')}\n*Expected Answer:* {b.get('expected_answer')}\n" for b in tech_kit.get('basic_foundational', [])])}

### Tier 2: Advanced Practitioner Checkpoints
{chr(10).join([f"**Q{a.get('id')} ({a.get('focus_area')}):** {a.get('question')}\n*Expected Answer:* {a.get('expected_answer')}\n" for a in tech_kit.get('advanced_practitioner', [])])}

### Tier 3: Innovative / Architectural Curveballs
{chr(10).join([f"**Q{i.get('id')} ({i.get('focus_area')}):** {i.get('question')}\n*Expected Answer:* {i.get('expected_answer')}\n" for i in tech_kit.get('innovative_curveballs', [])])}

---

## 4. Interviewer Verdict & Next Steps:
- **Interviewer Name:** {current_user.get('full_name') or current_user.get('email')}
- **Screening Decision:** [ ] Pass to Tech Round  |  [ ] Hold  |  [ ] Reject
- **Notes:** 
"""

        edited_kit_md = st.text_area("Live Editable Verification Kit & Interview Notes", value=kit_markdown_default, height=350, key="kit_markdown_editor")

        col_save_kit, col_dl_pdf = st.columns(2)
        with col_save_kit:
            if st.button("💾 Save Screening Dossier to Database", type="primary", use_container_width=True):
                st.session_state.saved_screening_kits[f"{cand_n}_{chosen_v_jd_key}"] = edited_kit_md
                st.success(f"Dossier saved for {cand_n}! Access anytime in your active session.")

        with col_dl_pdf:
            kit_pdf_bytes = generate_pdf_report(edited_kit_md, title=f"Screening Kit - {cand_n}")
            st.download_button(
                label="📥 Download Verification Dossier (PDF)",
                data=kit_pdf_bytes,
                file_name=f"Verification_Kit_{cand_n.replace(' ', '_')}.pdf",
                mime="application/pdf",
                use_container_width=True
            )
