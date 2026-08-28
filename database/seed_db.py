import json
import uuid
from datetime import datetime, timedelta
from database.sql_models import Base, User, JobDescription, Resume, Application
from database.sql_db import sql_db, SessionLocal, engine
from database.chroma_db import chroma
from core.sample_data import SAMPLE_JDS, SAMPLE_RESUMES


def seed_database():
    """
    Idempotent seeding script populating SQLite/PostgreSQL and ChromaDB
    with default user accounts, active JDs, candidate resumes, and interview logs.
    """
    # Ensure all tables exist prior to seeding
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    
    print("=" * 60)
    print("Initiating PragyanAI Database Seeding Engine...")
    print("=" * 60)

    try:
        # 1. Seed Default User Accounts
        default_users = [
            ("admin@pragyan.ai", "admin123", "admin", "System Administrator", True),
            ("candidate@pragyan.ai", "candidate123", "candidate", "Aarav Sharma", True),
            ("recruiter@enterprise.com", "company123", "company", "Apex AI Labs HR", True),
            ("pending_recruiter@startup.io", "company123", "company", "NextGen Startup", False),
        ]

        for email, pwd, role, name, approved in default_users:
            normalized_email = email.strip().lower()
            user = session.query(User).filter(User.email == normalized_email).first()
            if not user:
                new_user = User(
                    email=normalized_email,
                    password_hash=sql_db.hash_password(pwd),
                    role=role,
                    full_name=name,
                    is_approved=approved
                )
                session.add(new_user)
                print(f"[+] Created User: {normalized_email} ({role})")
        session.commit()

        candidate_user = session.query(User).filter(User.email == "candidate@pragyan.ai").first()

        # 2. Seed Job Descriptions & Vector Index
        jd_id_map = {}
        for jd_data in SAMPLE_JDS:
            existing_jd = session.query(JobDescription).filter(JobDescription.title == jd_data["title"]).first()
            if not existing_jd:
                new_jd = JobDescription(
                    title=jd_data["title"],
                    department=jd_data["department"],
                    location_type=jd_data["location_type"],
                    content=jd_data["content"]
                )
                session.add(new_jd)
                session.commit()
                session.refresh(new_jd)
                jd_id_map[new_jd.title] = new_jd.id

                # Upsert into ChromaDB
                chroma.upsert_jd(
                    doc_id=f"jd_{new_jd.id}",
                    text=new_jd.content,
                    metadata={"title": new_jd.title, "type": "jd", "sql_id": new_jd.id}
                )
                print(f"[+] Ingested & Vectorized JD: {new_jd.title}")
            else:
                jd_id_map[existing_jd.title] = existing_jd.id

        # 3. Seed Candidate Resumes, Vector Index & Applications
        for cand in SAMPLE_RESUMES:
            existing_res = session.query(Resume).filter(Resume.filename == cand["filename"]).first()
            assigned_user_id = candidate_user.id if cand["candidate_name"] == "Aarav Sharma" and candidate_user else None

            if not existing_res:
                new_res = Resume(
                    user_id=assigned_user_id,
                    filename=cand["filename"],
                    raw_content=cand["raw_content"],
                    markdown_content=cand["raw_content"]
                )
                session.add(new_res)
                session.commit()
                session.refresh(new_res)

                # Upsert into ChromaDB
                chroma.upsert_resume(
                    doc_id=f"resume_{new_res.id}",
                    text=new_res.raw_content,
                    metadata={
                        "filename": new_res.filename,
                        "candidate_name": cand["candidate_name"],
                        "type": "resume",
                        "sql_id": new_res.id
                    }
                )
                print(f"[+] Ingested & Vectorized Resume: {cand['filename']}")

                # 4. Link Application Record
                matched_jd_id = list(jd_id_map.values())[0] if jd_id_map else None
                score = 94.5 if "Lead" in cand["filename"] else 42.0
                stage = "Scheduled" if score > 75 else "Applied"

                new_app = Application(
                    candidate_id=assigned_user_id,
                    candidate_name=cand["candidate_name"],
                    candidate_email=cand["email"],
                    jd_id=matched_jd_id,
                    match_score=score,
                    swot_json=json.dumps(cand["swot"]),
                    stage=stage,
                    interview_type="Round 1: AI Technical Assessment" if stage == "Scheduled" else None,
                    interview_time=datetime.utcnow() + timedelta(days=2, hours=4) if stage == "Scheduled" else None,
                    meeting_link=f"https://meet.jit.si/Interview_{uuid.uuid4().hex[:8]}" if stage == "Scheduled" else None,
                    agenda_notes="Probe LangGraph cyclical execution and local FAISS vector store scaling." if stage == "Scheduled" else None
                )
                session.add(new_app)
                session.commit()
                print(f"[+] Created Application Pipeline Record: {cand['candidate_name']} ({stage})")

        print("=" * 60)
        print("Database & ChromaDB Vector Store Seeded Successfully.")
        print("Default Accounts:")
        print("  - Admin:     admin@pragyan.ai / admin123")
        print("  - Candidate: candidate@pragyan.ai / candidate123")
        print("  - Employer:  recruiter@enterprise.com / company123")
        print("=" * 60)

    except Exception as e:
        session.rollback()
        print(f"[!] Error during database seeding: {str(e)}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    seed_database()
