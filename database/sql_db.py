import hashlib
from typing import Optional, Dict, Any, List
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from config.settings import settings
from database.sql_models import Base, User, JobDescription, Resume, Application

# Connect Arguments (SQLite needs check_same_thread=False for multi-threaded Streamlit workers)
connect_args = {"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True
)

SessionLocal = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))

# Ensure all relational tables exist on startup
Base.metadata.create_all(bind=engine)


class SQLDatabaseManager:
    """Manages transactional sessions, user authentication, and data operations."""

    @staticmethod
    def get_session():
        """Returns a thread-safe database session."""
        return SessionLocal()

    @staticmethod
    def hash_password(password: str) -> str:
        """Computes SHA-256 hash for secure credential storage."""
        return hashlib.sha256(password.encode("utf-8")).hexdigest()

    def register_user(
        self,
        email: str,
        password: str,
        role: str,
        full_name: str = ""
    ) -> Dict[str, Any]:
        """Registers a new user. Candidates are auto-approved; Companies require moderation."""
        session = self.get_session()
        try:
            normalized_email = email.strip().lower()
            existing_user = session.query(User).filter(User.email == normalized_email).first()
            if existing_user:
                return {"success": False, "message": "Email is already registered."}

            is_approved = True if role == "candidate" else False

            new_user = User(
                email=normalized_email,
                password_hash=self.hash_password(password),
                role=role,
                full_name=full_name.strip(),
                is_approved=is_approved
            )
            session.add(new_user)
            session.commit()
            session.refresh(new_user)

            return {
                "success": True,
                "user": {
                    "id": new_user.id,
                    "email": new_user.email,
                    "role": new_user.role,
                    "full_name": new_user.full_name,
                    "is_approved": new_user.is_approved
                }
            }
        except Exception as e:
            session.rollback()
            return {"success": False, "message": f"Database error: {str(e)}"}
        finally:
            session.close()

    def authenticate_user(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        """Verifies credentials and returns user payload if valid."""
        session = self.get_session()
        try:
            normalized_email = email.strip().lower()
            pwd_hash = self.hash_password(password)
            user = session.query(User).filter(
                User.email == normalized_email,
                User.password_hash == pwd_hash
            ).first()

            if user:
                return {
                    "id": user.id,
                    "email": user.email,
                    "role": user.role,
                    "full_name": user.full_name,
                    "is_approved": user.is_approved
                }
            return None
        finally:
            session.close()

    def save_resume(
        self,
        filename: str,
        raw_content: str,
        markdown_content: str = "",
        user_id: Optional[int] = None
    ) -> int:
        """Persists a resume record."""
        session = self.get_session()
        try:
            resume = Resume(
                user_id=user_id,
                filename=filename,
                raw_content=raw_content,
                markdown_content=markdown_content or raw_content
            )
            session.add(resume)
            session.commit()
            session.refresh(resume)
            return resume.id
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def save_job_description(
        self,
        title: str,
        content: str,
        department: str = "Engineering",
        location_type: str = "Remote"
    ) -> int:
        """Persists a job description record."""
        session = self.get_session()
        try:
            jd = JobDescription(
                title=title,
                department=department,
                location_type=location_type,
                content=content
            )
            session.add(jd)
            session.commit()
            session.refresh(jd)
            return jd.id
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def create_application(
        self,
        candidate_name: str,
        candidate_email: str,
        match_score: float,
        swot_json: str,
        stage: str = "Applied",
        candidate_id: Optional[int] = None,
        jd_id: Optional[int] = None,
        interview_type: Optional[str] = None,
        interview_time: Optional[Any] = None,
        meeting_link: Optional[str] = None,
        agenda_notes: Optional[str] = None
    ) -> int:
        """Creates an application tracking record with optional interview details."""
        session = self.get_session()
        try:
            app = Application(
                candidate_id=candidate_id,
                candidate_name=candidate_name,
                candidate_email=candidate_email,
                jd_id=jd_id,
                match_score=match_score,
                swot_json=swot_json,
                stage=stage,
                interview_type=interview_type,
                interview_time=interview_time,
                meeting_link=meeting_link,
                agenda_notes=agenda_notes
            )
            session.add(app)
            session.commit()
            session.refresh(app)
            return app.id
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()


# Global SQL manager singleton
sql_db = SQLDatabaseManager()
