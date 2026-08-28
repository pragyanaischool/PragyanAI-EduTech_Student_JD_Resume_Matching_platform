import streamlit as st
import pandas as pd
import plotly.express as px
from database.sql_models import User, JobDescription, Application, Resume
from database.sql_db import sql_db, SessionLocal, engine
from database.chroma_db import chroma
from core.parsers import parse_pdf, parse_docx, parse_url

st.set_page_config(page_title="Admin Control Center", layout="wide", page_icon="👑")

# Session Authorization Guard
if "auth_user" not in st.session_state or not st.session_state.auth_user:
    st.warning("Please sign in from the main portal to access the Admin Control Center.")
    st.stop()

if st.session_state.auth_user.get("role") != "admin":
    st.error(f"Access Denied. Role '{st.session_state.auth_user.get('role').upper()}' is not authorized for Admin Console.")
    st.stop()

st.title("Admin Global Governance & Telemetry")
st.caption("Platform telemetry, tenant onboarding moderation, and global knowledge base ingestion.")

tab_metrics, tab_approvals, tab_ingest, tab_records = st.tabs([
    "📊 Platform Telemetry", 
    "🛡️ Tenant Approvals", 
    "📥 Universal Ingestion Vault",
    "🗄️ System Database Explorer"
])

session = SessionLocal()

try:
    # ----------------- TAB 1: TELEMETRY & CONVERSION FUNNEL -----------------
    with tab_metrics:
        st.subheader("Global Platform Metrics")
        c1, c2, c3, c4 = st.columns(4)
        
        total_candidates = session.query(User).filter(User.role == "candidate").count()
        total_companies = session.query(User).filter(User.role == "company").count()
        total_jds = session.query(JobDescription).count()
        total_apps = session.query(Application).count()
        
        c1.metric("Registered Candidates", total_candidates)
        c2.metric("Hiring Companies", total_companies)
        c3.metric("Indexed JDs", total_jds)
        c4.metric("Total Applications", total_apps)
        
        st.markdown("---")
        
        col_chart1, col_chart2 = st.columns(2)
        with col_chart1:
            stage_counts = {
                "Applied": session.query(Application).count(),
                "Pre-Screen Passed": session.query(Application).filter(Application.stage.in_(["Pre-Screen Passed", "Scheduled", "Hired"])).count(),
                "Interview Scheduled": session.query(Application).filter(Application.stage.in_(["Scheduled", "Hired"])).count(),
                "Hired / Offers": session.query(Application).filter(Application.stage == "Hired").count()
            }
            df_funnel = pd.DataFrame({
                "Stage": list(stage_counts.keys()),
                "Candidates": list(stage_counts.values())
            })
            fig_funnel = px.funnel(df_funnel, x="Candidates", y="Stage", title="Candidate Conversion Funnel")
            st.plotly_chart(fig_funnel, use_container_width=True)

        with col_chart2:
            roles_data = {
                "Candidates": total_candidates,
                "Hiring Companies": total_companies,
                "Admins": session.query(User).filter(User.role == "admin").count()
            }
            df_roles = pd.DataFrame({"Role": list(roles_data.keys()), "Count": list(roles_data.values())})
            fig_pie = px.pie(df_roles, names="Role", values="Count", title="Platform User Distribution", hole=0.4)
            st.plotly_chart(fig_pie, use_container_width=True)

    # ----------------- TAB 2: TENANT ONBOARDING APPROVALS -----------------
    with tab_approvals:
        st.subheader("Tenant & Employer Moderation Queue")
        pending_users = session.query(User).filter(User.is_approved == False).all()
        
        if pending_users:
            pending_data = [{
                "User ID": u.id,
                "Email": u.email,
                "Full Name / Org": u.full_name or "N/A",
                "Role": u.role.upper(),
                "Registered At": u.created_at.strftime("%Y-%m-%d %H:%M") if u.created_at else "N/A"
            } for u in pending_users]
            
            st.dataframe(pd.DataFrame(pending_data), use_container_width=True)
            
            col_app1, col_app2 = st.columns([2, 1])
            with col_app1:
                selected_user_id = st.selectbox(
                    "Select Account to Moderate",
                    [p["User ID"] for p in pending_data],
                    format_func=lambda x: f"User ID #{x} - {next(p['Email'] for p in pending_data if p['User ID'] == x)}"
                )
            
            with col_app2:
                st.write(" ")
                st.write(" ")
                c_btn1, c_btn2 = st.columns(2)
                if c_btn1.button("Approve Tenant", type="primary", use_container_width=True):
                    target_user = session.query(User).filter(User.id == selected_user_id).first()
                    if target_user:
                        target_user.is_approved = True
                        session.commit()
                        st.success(f"Approved access for {target_user.email}")
                        st.rerun()
                if c_btn2.button("Reject / Delete", use_container_width=True):
                    target_user = session.query(User).filter(User.id == selected_user_id).first()
                    if target_user:
                        session.delete(target_user)
                        session.commit()
                        st.warning(f"Deleted account application for {target_user.email}")
                        st.rerun()
        else:
            st.info("Zero pending moderation requests. All employer and candidate accounts are authorized.")

    # ----------------- TAB 3: UNIVERSAL INGESTION VAULT -----------------
    with tab_ingest:
        st.subheader("Direct Document Vectorization & Database Registration")
        col_in1, col_in2 = st.columns([1, 1])
        
        with col_in1:
            ingest_asset = st.radio("Asset Classification", ["Job Description (JD)", "Candidate Resume"], horizontal=True)
            source_mode = st.selectbox("Ingestion Pathway", ["Upload Document (PDF/DOCX)", "Scrape Web / LinkedIn URL", "Direct Text Paste"])
            
            raw_ingest_text = ""
            if source_mode == "Upload Document (PDF/DOCX)":
                up_f = st.file_uploader("Upload Target File", type=["pdf", "docx"], key="admin_uploader")
                if up_f:
                    raw_ingest_text = parse_pdf(up_f.read()) if up_f.name.endswith(".pdf") else parse_docx(up_f.read())
            elif source_mode == "Scrape Web / LinkedIn URL":
                url_in = st.text_input("Posting URL", placeholder="https://careers.company.com/job/...")
                if url_in and st.button("Extract Body Text"):
                    with st.spinner("Scraping URL body content..."):
                        raw_ingest_text = parse_url(url_in)
                        st.success("Extracted text successfully.")
            else:
                raw_ingest_text = st.text_area("Paste Content Text", height=220)

        with col_in2:
            doc_title_in = st.text_input("Document Name / Identifier", value="Position_Lead_ML_Engineer")
            dept_in = st.text_input("Department / Vertical", value="Advanced AI Systems")
            loc_type = st.selectbox("Position Location Type", ["Remote", "Hybrid", "Onsite"])
            
            if st.button("Save to SQL & ChromaDB Vector Store", type="primary", use_container_width=True):
                if raw_ingest_text.strip():
                    with st.spinner("Saving relational record and computing vector embeddings..."):
                        if "JD" in ingest_asset:
                            new_jd_rec = JobDescription(
                                title=doc_title_in,
                                department=dept_in,
                                location_type=loc_type,
                                content=raw_ingest_text
                            )
                            session.add(new_jd_rec)
                            session.commit()
                            session.refresh(new_jd_rec)
                            chroma.upsert_jd(
                                doc_id=f"jd_{new_jd_rec.id}",
                                text=raw_ingest_text,
                                metadata={"title": doc_title_in, "type": "jd", "sql_id": new_jd_rec.id}
                            )
                        else:
                            new_res_rec = Resume(
                                filename=f"{doc_title_in}.txt",
                                raw_content=raw_ingest_text,
                                markdown_content=raw_ingest_text
                            )
                            session.add(new_res_rec)
                            session.commit()
                            session.refresh(new_res_rec)
                            chroma.upsert_resume(
                                doc_id=f"resume_{new_res_rec.id}",
                                text=raw_ingest_text,
                                metadata={"filename": new_res_rec.filename, "type": "resume", "sql_id": new_res_rec.id}
                            )
                        st.success(f"{ingest_asset} successfully indexed into SQL and ChromaDB vector store.")
                else:
                    st.warning("Please provide valid text content before saving.")

    # ----------------- TAB 4: DATABASE RECORD EXPLORER -----------------
    with tab_records:
        st.subheader("Relational Database Inspection")
        view_table = st.selectbox("Select SQL Table to Query", ["Users", "Job Descriptions", "Resumes", "Applications Pipeline"])
        
        if view_table == "Users":
            users_list = session.query(User).all()
            if users_list:
                df_u = pd.DataFrame([{
                    "ID": u.id, "Email": u.email, "Role": u.role, "Full Name": u.full_name, "Approved": u.is_approved, "Created": u.created_at
                } for u in users_list])
                st.dataframe(df_u, use_container_width=True)
        elif view_table == "Job Descriptions":
            jds_list = session.query(JobDescription).all()
            if jds_list:
                df_j = pd.DataFrame([{
                    "ID": j.id, "Title": j.title, "Department": j.department, "Location": j.location_type, "Created": j.created_at
                } for j in jds_list])
                st.dataframe(df_j, use_container_width=True)
        elif view_table == "Resumes":
            res_list = session.query(Resume).all()
            if res_list:
                df_r = pd.DataFrame([{
                    "ID": r.id, "User ID": r.user_id, "Filename": r.filename, "Created": r.created_at
                } for r in res_list])
                st.dataframe(df_r, use_container_width=True)
        elif view_table == "Applications Pipeline":
            apps_list = session.query(Application).all()
            if apps_list:
                df_a = pd.DataFrame([{
                    "ID": a.id, "Candidate": a.candidate_name, "Email": a.candidate_email, "Score": a.match_score, "Stage": a.stage, "Interview": a.interview_type, "Meeting Link": a.meeting_link
                } for a in apps_list])
                st.dataframe(df_a, use_container_width=True)

finally:
    session.close()
