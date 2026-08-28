import streamlit as st
from database.sql_db import sql_db
from core.parsers import parse_pdf, parse_docx
from core.pdf_builder import generate_pdf_report
from core.prompt_engine import (
    build_markdown_resume,
    extract_resume_sections,
    update_resume_section,
    refine_resume_section,
)


def render_step1(current_user: dict):
    st.header("Step 1: Resume Ingestion & 3-Box Copilot Studio")
    st.caption("Ingest existing credentials, polish sections using active verbs and metrics, and export publication-ready ATS PDF or Markdown.")

    col_in, col_status = st.columns([1, 1])

    with col_in:
        st.subheader("1. Ingest Profile Data")
        upload_cv_file = st.file_uploader(
            "Upload Existing Resume (PDF / DOCX)", 
            type=["pdf", "docx"], 
            key="step1_upload_cv"
        )
        raw_notes_input = st.text_area(
            "Or Paste Raw Profile / Career Notes", 
            height=140, 
            placeholder="Paste work history, core tech stack, achievements, education, certifications..."
        )

        c_gh, c_li = st.columns(2)
        github_input = c_gh.text_input("GitHub Profile URL", placeholder="https://github.com/...")
        linkedin_input = c_li.text_input("LinkedIn Profile URL", placeholder="https://linkedin.com/in/...")

        if st.button("🚀 Ingest & Build Master Resume", type="primary", use_container_width=True):
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
                    st.session_state.master_rev += 1

                    fresh_sections = extract_resume_sections(transformed_cv)
                    st.session_state.sec_current = fresh_sections.copy()
                    st.session_state.sec_ai = {}
                    st.session_state.sec_mod = fresh_sections.copy()
                    for k in fresh_sections:
                        st.session_state.sec_polish_rev[k] = 0

                    sql_db.save_resume(
                        filename=filename,
                        raw_content=raw_content,
                        markdown_content=transformed_cv,
                        user_id=current_user.get("id")
                    )
                    st.success("Master resume synthesized and loaded!")
                    st.rerun()
            else:
                st.warning("Please upload a file or paste profile notes.")

    with col_status:
        st.subheader("2. Profile Ingestion Status")
        if st.session_state.cand_cv:
            st.success("✅ Master Resume is active and loaded.")
            extracted_count = len([k for k, v in st.session_state.sec_current.items() if v.strip()])
            st.markdown(f"**Extracted Sections:** `{extracted_count}` | **Active Revision:** `#{st.session_state.master_rev}`")
            st.info("Use the 3-Box Copilot below to polish specific sections, then view and download the full merged document at the bottom.")
        else:
            st.info("No master resume active. Ingest your resume on the left to start.")

    st.markdown("---")

    # ==========================================================================
    # 3-Box Section Polish Copilot
    # ==========================================================================
    if st.session_state.cand_cv:
        st.subheader("🛠️ 3-Box Section Polish Copilot")
        st.caption("Review extracted sections, generate AI polish with Google X-Y-Z formula, tweak in the Modified box, and apply directly to your Master Resume.")
        m_rev = st.session_state.master_rev

        t_sum, t_skl, t_exp, t_prj, t_edu = st.tabs([
            "📝 Executive Summary",
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
                c1, c2, c3 = st.columns([1, 1, 1])
                p_rev = st.session_state.sec_polish_rev.get(sec_name, 0)

                curr_val = st.session_state.sec_current.get(sec_name, "")
                ai_val = st.session_state.sec_ai.get(sec_name, "")
                mod_val = st.session_state.sec_mod.get(sec_name, curr_val)

                # --- BOX 1: CURRENT EXTRACTED ---
                with c1:
                    st.markdown(f"**1️⃣ Current {sec_name}:**")
                    edited_curr = st.text_area(
                        f"Current {sec_name}", 
                        value=curr_val, 
                        height=200, 
                        key=f"box1_{sec_name}_{m_rev}_{p_rev}",
                        placeholder=f"Enter or edit existing {sec_name} text..."
                    )
                    st.session_state.sec_current[sec_name] = edited_curr

                    if st.button(f"✨ {btn_label}", key=f"btn_p_{sec_name}_{m_rev}_{p_rev}", type="primary", use_container_width=True):
                        text_to_refine = edited_curr.strip() or f"Candidate profile, skills, and achievements in {sec_name}."
                        with st.spinner(f"Polishing {sec_name} with Groq LLM..."):
                            polished_out = refine_resume_section(sec_name, text_to_refine)
                            st.session_state.sec_ai[sec_name] = polished_out
                            st.session_state.sec_mod[sec_name] = polished_out
                            st.session_state.sec_polish_rev[sec_name] = p_rev + 1
                            st.rerun()

                # --- BOX 2: AI REFINED DRAFT ---
                with c2:
                    st.markdown(f"**2️⃣ AI Refined Draft:**")
                    st.text_area(
                        f"AI Draft {sec_name}", 
                        value=ai_val, 
                        height=200, 
                        key=f"box2_{sec_name}_{m_rev}_{p_rev}", 
                        placeholder="Generated AI polish will appear here..."
                    )
                    if ai_val and st.button(f"Copy to Modified ➡️", key=f"btn_c_{sec_name}_{m_rev}_{p_rev}", use_container_width=True):
                        st.session_state.sec_mod[sec_name] = ai_val
                        st.session_state.sec_polish_rev[sec_name] = p_rev + 1
                        st.rerun()

                # --- BOX 3: MODIFIED & FINAL MERGE ---
                with c3:
                    st.markdown(f"**3️⃣ Modified / Final {sec_name}:**")
                    edited_mod = st.text_area(
                        f"Modified {sec_name}", 
                        value=mod_val, 
                        height=200, 
                        key=f"box3_{sec_name}_{m_rev}_{p_rev}",
                        placeholder="Customize final text here before applying to master..."
                    )
                    st.session_state.sec_mod[sec_name] = edited_mod

                    if st.button(f"💾 Apply Modified {sec_name}", key=f"btn_a_{sec_name}_{m_rev}_{p_rev}", type="primary", use_container_width=True):
                        if edited_mod.strip():
                            updated_cv = update_resume_section(st.session_state.cand_cv, sec_name, edited_mod)
                            st.session_state.cand_cv = updated_cv
                            st.session_state.master_rev += 1
                            st.session_state.sec_current[sec_name] = edited_mod
                            st.session_state.sec_mod[sec_name] = edited_mod
                            st.session_state.sec_polish_rev[sec_name] = p_rev + 1

                            sql_db.save_resume(
                                filename="Updated_Resume.md", 
                                raw_content=updated_cv, 
                                markdown_content=updated_cv, 
                                user_id=current_user.get("id")
                            )
                            st.success(f"Applied {sec_name} to Master Resume!")
                            st.rerun()
                        else:
                            st.warning("Modified section cannot be empty.")

        # ======================================================================
        # Full Document Preview & Dual Export
        # ======================================================================
        st.markdown("---")
        st.subheader("📄 Full Master Resume Preview & Dual Export")
        c_md, c_pdf = st.columns([1, 1])

        with c_md:
            st.markdown("#### 📝 Editable Markdown Source")
            master_val = st.text_area(
                "Master Markdown Document", 
                value=st.session_state.cand_cv, 
                height=340, 
                key=f"step1_full_md_{m_rev}"
            )
            if master_val != st.session_state.cand_cv:
                st.session_state.cand_cv = master_val

            st.download_button(
                label="📥 Download Resume (.MD)",
                data=st.session_state.cand_cv.encode("utf-8"),
                file_name="Master_ATS_Resume.md",
                mime="text/markdown",
                use_container_width=True
            )

        with c_pdf:
            st.markdown("#### 👁️ Live Rendered Document")
            with st.container(height=340, border=True):
                st.markdown(st.session_state.cand_cv)

            pdf_bytes = generate_pdf_report(st.session_state.cand_cv, title="Curriculum Vitae")
            st.download_button(
                label="📥 Download Publication-Ready ATS PDF",
                data=pdf_bytes,
                file_name="Master_ATS_Resume.pdf",
                mime="application/pdf",
                type="primary",
                use_container_width=True
            )
