from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

def utcnow():
    return datetime.now(timezone.utc)

class JobProfileDB(Base):
    __tablename__ = "job_profiles"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String(255), nullable=False, index=True)
    department = Column(String(100), nullable=True)
    min_experience_years = Column(Float, default=0.0)
    min_education = Column(String(100), default="Bachelor's")
    required_skills = Column(Text, default="[]")       # JSON array of strings
    nice_to_have_skills = Column(Text, default="[]")   # JSON array of strings
    description = Column(Text, nullable=False)
    created_at = Column(DateTime, default=utcnow)

    rankings = relationship("RankingResultDB", back_populates="job", cascade="all, delete-orphan")


class ResumeDB(Base):
    __tablename__ = "resumes"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    filename = Column(String(255), nullable=False)
    file_type = Column(String(20), nullable=False)     # pdf, docx, txt
    file_size = Column(Integer, default=0)             # bytes
    file_path = Column(String(500), nullable=True)
    raw_text = Column(Text, nullable=False)
    cleaned_text = Column(Text, nullable=False)
    anonymized_text = Column(Text, nullable=True)      # Phase 2: Redacted text
    structured_data = Column(Text, nullable=True)      # Phase 2: JSON representation
    redactions_count = Column(Integer, default=0)      # Phase 2: Total PII/institution redactions
    char_count = Column(Integer, default=0)
    word_count = Column(Integer, default=0)
    ocr_used = Column(Boolean, default=False)
    created_at = Column(DateTime, default=utcnow)

    rankings = relationship("RankingResultDB", back_populates="resume", cascade="all, delete-orphan")


class RankingResultDB(Base):
    __tablename__ = "ranking_results"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    job_id = Column(Integer, ForeignKey("job_profiles.id"), nullable=False, index=True)
    resume_id = Column(Integer, ForeignKey("resumes.id"), nullable=False, index=True)
    similarity_score = Column(Float, nullable=False)   # Final weighted score
    rank = Column(Integer, nullable=False)
    
    # Phase 2: Multi-factor breakdown
    skills_score = Column(Float, default=0.0)
    experience_score = Column(Float, default=0.0)
    projects_score = Column(Float, default=0.0)
    education_score = Column(Float, default=0.0)
    hard_flags = Column(Text, default="[]")            # JSON array of strings
    
    matched_skills = Column(Text, default="[]")        # JSON array
    missing_skills = Column(Text, default="[]")        # JSON array

    # Phase 3: HR Workflow & Explainability
    hr_status = Column(String(50), default="Shortlisted") # Shortlisted, Review Manually, Interview Approved, Rejected
    hr_notes = Column(Text, default="")
    identity_revealed = Column(Boolean, default=False)
    strengths_json = Column(Text, default="[]")
    gaps_json = Column(Text, default="[]")
    interview_questions_json = Column(Text, default="[]")

    created_at = Column(DateTime, default=utcnow)

    job = relationship("JobProfileDB", back_populates="rankings")
    resume = relationship("ResumeDB", back_populates="rankings")
