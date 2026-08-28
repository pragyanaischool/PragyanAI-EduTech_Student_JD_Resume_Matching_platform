import streamlit as st
import pandas as pd
from core.sample_data import SAMPLE_JDS, SAMPLE_RESUMES
from core.pdf_builder import generate_pdf_report
from core.generate_sample_files import create_docx, build_all_cvs_and_jds_zip

st.set_page_config(page_title="Sample Datasets & Downloads", layout="wide", page_icon="📦")

st.title("Sample Dataset Library: 10 CVs & 10 JDs")
st.caption("Download individual candidate resumes and job descriptions as ATS-compliant PDFs or DOCX files, or download the entire bundled archive.")

# Bulk Download Card
st.markdown("### Master Bundle Download")
col_b1, col_b2 = st.columns([2, 1])
with col_b1:
    st.info("Download all **10 Candidate CVs** and **10 Job Descriptions** bundled together in both **PDF** and **DOCX** formats.")
with col_b2:
    with st.spinner("Preparing ZIP package..."):
        zip_bytes = build_all_cvs_and_jds_zip()
    st.download_button(
        label="Download All 20 Documents (ZIP)",
        data=zip_bytes,
        file_name="PragyanAI_10_CVs_10_JDs_Master_Bundle.zip",
        mime="application/zip",
        type="primary",
        use_container_width=True
    )

st.divider()

tab_cvs, tab_jds = st.tabs(["📄 10 Candidate Resumes (CVs)", "📋 10 Job Descriptions (JDs)"])

# ----------------- TAB 1: 10 RESUMES -----------------
with tab_cvs:
    st.subheader("Browse & Download 10 Candidate CVs")
    for idx, cv in enumerate(SAMPLE_RESUMES, start=1):
        with st.expander(f"CV #{idx:02d}: {cv['candidate_name']} — {cv['target_role']}"):
            c1, c2 = st.columns([3, 1])
            with c1:
                st.text_area(f"Raw Resume Content ({cv['candidate_name']})", value=cv["raw_content"], height=200, key=f"raw_cv_{idx}")
            with c2:
                st.write("**Export Document:**")
                pdf_b = generate_pdf_report(cv["raw_content"], title=f"Curriculum Vitae - {cv['candidate_name']}")
                docx_b = create_docx(f"Curriculum Vitae - {cv['candidate_name']}", cv["raw_content"])
                
                st.download_button(
                    label="Download PDF",
                    data=pdf_b,
                    file_name=f"{cv['candidate_name'].replace(' ', '_')}_Resume.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                    key=f"dl_pdf_cv_{idx}"
                )
                st.download_button(
                    label="Download DOCX",
                    data=docx_b,
                    file_name=f"{cv['candidate_name'].replace(' ', '_')}_Resume.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    use_container_width=True,
                    key=f"dl_docx_cv_{idx}"
                )

# ----------------- TAB 2: 10 JOB DESCRIPTIONS -----------------
with tab_jds:
    st.subheader("Browse & Download 10 Job Descriptions")
    for idx, jd in enumerate(SAMPLE_JDS, start=1):
        with st.expander(f"JD #{idx:02d}: {jd['title']} ({jd['department']})"):
            c1, c2 = st.columns([3, 1])
            with c1:
                st.text_area(f"Raw Job Spec ({jd['title']})", value=jd["content"], height=200, key=f"raw_jd_{idx}")
            with c2:
                st.write("**Export Document:**")
                pdf_b = generate_pdf_report(jd["content"], title=f"Job Specification - {jd['title']}")
                docx_b = create_docx(f"Job Specification - {jd['title']}", jd["content"])

                st.download_button(
                    label="Download PDF",
                    data=pdf_b,
                    file_name=f"{jd['title'].replace(' ', '_').replace('/', '_')}_JD.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                    key=f"dl_pdf_jd_{idx}"
                )
                st.download_button(
                    label="Download DOCX",
                    data=docx_b,
                    file_name=f"{jd['title'].replace(' ', '_').replace('/', '_')}_JD.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    use_container_width=True,
                    key=f"dl_docx_jd_{idx}"
                )
