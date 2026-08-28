from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Float,
    Boolean,
    DateTime,
    ForeignKey
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False, default="candidate")  # 'admin' | 'candidate' | 'company'
    full_name = Column(String(255), default="")
    is_approved = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    resumes = relationship("Resume", back_populates="user", cascade="all, delete-orphan")
    applications = relationship("Application", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User id={self.id} email='{self.email}' role='{self.role}'>"


class JobDescription(Base):
    __tablename__ = "job_descriptions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False, index=True)
    department = Column(String(100), default="Engineering")
    location_type = Column(String(50), default="Remote")  # 'Remote' | 'Hybrid' | 'Onsite'
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    applications = relationship("Application", back_populates="jd", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<JobDescription id={self.id} title='{self.title}'>"


class Resume(Base):
    __tablename__ = "resumes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    filename = Column(String(255), nullable=False)
    raw_content = Column(Text, nullable=False)
    markdown_content = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="resumes")

    def __repr__(self):
        return f"<Resume id={self.id} filename='{self.filename}'>"


class Application(Base):
    __tablename__ = "applications"

    id = Column(Integer, primary_key=True, autoincrement=True)
    candidate_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    candidate_name = Column(String(255), nullable=False)
    candidate_email = Column(String(255), nullable=False, index=True)
    jd_id = Column(Integer, ForeignKey("job_descriptions.id", ondelete="SET NULL"), nullable=True)
    match_score = Column(Float, default=0.0)
    swot_json = Column(Text, nullable=True)  # Serialized SWOT matrix & keyword data
    stage = Column(String(50), default="Applied")  # 'Applied' | 'Pre-Screen Passed' | 'Scheduled' | 'Hired' | 'Rejected'
    
    # Interview Scheduling Data
    interview_type = Column(String(100), nullable=True)
    interview_time = Column(DateTime, nullable=True)
    meeting_link = Column(String(255), nullable=True)
    agenda_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="applications")
    jd = relationship("JobDescription", back_populates="applications")

    def __repr__(self):
        return f"<Application id={self.id} candidate='{self.candidate_name}' stage='{self.stage}'>"
