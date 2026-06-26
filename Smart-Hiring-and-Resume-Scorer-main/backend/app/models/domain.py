from sqlalchemy import Column, String, Integer, Float, Text, DateTime, ForeignKey, Boolean, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from ..database import Base

def gen_uuid():
    return str(uuid.uuid4())

class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True, default=gen_uuid)
    email = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, default="")
    role = Column(String, default="recruiter")  # admin / recruiter
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    jobs = relationship("Job", back_populates="creator")
    candidate_profile = relationship("CandidateProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")

class Job(Base):
    __tablename__ = "jobs"
    id = Column(String, primary_key=True, default=gen_uuid)
    created_by = Column(String, ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=False)
    company = Column(String, default="")
    jd_text = Column(Text, nullable=False)
    required_skills = Column(JSON, default=list)
    nice_to_have_skills = Column(JSON, default=list)
    min_years_exp = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())
    creator = relationship("User", back_populates="jobs")
    resumes = relationship("Resume", back_populates="job", cascade="all, delete-orphan")
    results = relationship("Result", back_populates="job", cascade="all, delete-orphan")
    applications = relationship("Application", back_populates="job", cascade="all, delete-orphan")

class Resume(Base):
    __tablename__ = "resumes"
    id = Column(String, primary_key=True, default=gen_uuid)
    job_id = Column(String, ForeignKey("jobs.id"), nullable=False)
    filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    extracted_text = Column(Text, default="")
    candidate_name = Column(String, default="")
    email = Column(String, default="")
    phone = Column(String, default="")
    sections = Column(JSON, default=dict)
    created_at = Column(DateTime, server_default=func.now())
    job = relationship("Job", back_populates="resumes")
    result = relationship("Result", back_populates="resume", uselist=False, cascade="all, delete-orphan")

class Result(Base):
    __tablename__ = "results"
    id = Column(String, primary_key=True, default=gen_uuid)
    job_id = Column(String, ForeignKey("jobs.id"), nullable=False)
    resume_id = Column(String, ForeignKey("resumes.id"), nullable=False)
    score = Column(Float, default=0.0)
    confidence = Column(Float, default=0.0)
    seniority = Column(String, default="Unknown")
    breakdown = Column(JSON, default=dict)
    evidence = Column(JSON, default=list)
    matched_skills = Column(JSON, default=list)
    missing_skills = Column(JSON, default=list)
    nice_to_have_found = Column(JSON, default=list)
    red_flags = Column(JSON, default=list)
    fraud_flags = Column(JSON, default=list)
    recommendations = Column(JSON, default=list)
    interview_questions = Column(JSON, default=list)
    project_evaluations = Column(JSON, default=list)
    explanation = Column(Text, default="")
    strength_tags = Column(JSON, default=list)
    status = Column(String, default="pending")  # pending/shortlisted/rejected/hold
    notes = Column(Text, default="")
    tags = Column(JSON, default=list)
    created_at = Column(DateTime, server_default=func.now())
    job = relationship("Job", back_populates="results")
    resume = relationship("Resume", back_populates="result")

class CandidateProfile(Base):
    __tablename__ = "candidate_profiles"
    id = Column(String, primary_key=True, default=gen_uuid)
    user_id = Column(String, ForeignKey("users.id"), unique=True, nullable=False)
    resume_path = Column(String, default="")
    filename = Column(String, default="")
    extracted_text = Column(Text, default="")
    extracted_skills = Column(JSON, default=list)
    contact_info = Column(JSON, default=dict)
    sections = Column(JSON, default=dict)
    overall_score = Column(Float, default=0.0)
    seniority = Column(String, default="")
    breakdown = Column(JSON, default=dict)
    strength_tags = Column(JSON, default=list)
    explanation = Column(Text, default="")
    project_evaluations = Column(JSON, default=list)
    fraud_flags = Column(JSON, default=list)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    user = relationship("User", back_populates="candidate_profile")
    applications = relationship("Application", back_populates="candidate", cascade="all, delete-orphan")

class Application(Base):
    __tablename__ = "applications"
    id = Column(String, primary_key=True, default=gen_uuid)
    candidate_id = Column(String, ForeignKey("candidate_profiles.id"), nullable=False)
    job_id = Column(String, ForeignKey("jobs.id"), nullable=False)
    score = Column(Float, default=0.0)
    match_percent = Column(Float, default=0.0)
    matched_skills = Column(JSON, default=list)
    missing_skills = Column(JSON, default=list)
    status = Column(String, default="pending")  # pending/shortlisted/rejected/interviewed
    breakdown = Column(JSON, default=dict)
    recommendations = Column(JSON, default=list)
    project_evaluations = Column(JSON, default=list)
    fraud_flags = Column(JSON, default=list)
    strength_tags = Column(JSON, default=list)
    explanation = Column(Text, default="")
    seniority = Column(String, default="Unknown")
    applied_at = Column(DateTime, server_default=func.now())
    candidate = relationship("CandidateProfile", back_populates="applications")
    job = relationship("Job", back_populates="applications")

class Interview(Base):
    __tablename__ = "interviews"
    id = Column(String, primary_key=True, default=gen_uuid)
    result_id = Column(String, nullable=False, index=True) # Pointing to either Application.id or Result.id
    scheduled_at = Column(DateTime, nullable=False)
    duration_minutes = Column(Integer, default=60)
    meeting_link = Column(String, default="")
    notes = Column(Text, default="")
    status = Column(String, default="scheduled")  # scheduled/completed/cancelled
    created_at = Column(DateTime, server_default=func.now())

class AppSettings(Base):
    __tablename__ = "app_settings"
    id = Column(Integer, primary_key=True, default=1)
    retention_days = Column(Integer, default=90)
    fairness_guardrails = Column(Boolean, default=True)
    max_file_size_mb = Column(Integer, default=10)

class CandidateEmbedding(Base):
    __tablename__ = "candidate_embeddings"
    id = Column(String, primary_key=True, default=gen_uuid)
    candidate_id = Column(String, ForeignKey("candidate_profiles.id"), unique=True, nullable=False)
    embedding = Column(JSON, nullable=False) # Store float array as JSON safely
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

class CandidateGitHub(Base):
    __tablename__ = "candidate_github"
    id = Column(String, primary_key=True, default=gen_uuid)
    candidate_id = Column(String, ForeignKey("candidate_profiles.id"), unique=True, nullable=False)
    github_url = Column(String, nullable=False)
    username = Column(String, nullable=False)
    metrics = Column(JSON, default=dict) # stars, repos, latest_activity
    top_languages = Column(JSON, default=dict)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
