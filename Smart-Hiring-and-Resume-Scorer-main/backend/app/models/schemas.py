from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime

# Auth
class UserCreate(BaseModel):
    email: str
    password: str
    full_name: Optional[str] = ""
    role: Optional[str] = "recruiter"

class UserLogin(BaseModel):
    email: str
    password: str

class UserOut(BaseModel):
    id: str
    email: str
    full_name: str
    role: str
    created_at: datetime
    class Config: from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserOut

# Jobs
class JobCreate(BaseModel):
    title: str
    company: Optional[str] = ""
    jd_text: str
    required_skills: Optional[List[str]] = []
    nice_to_have_skills: Optional[List[str]] = []
    min_years_exp: Optional[int] = 0

class JobOut(BaseModel):
    id: str
    title: str
    company: str
    jd_text: str
    required_skills: List[str]
    nice_to_have_skills: List[str]
    min_years_exp: int
    created_at: datetime
    resume_count: Optional[int] = 0
    class Config: from_attributes = True

# Resumes
class ResumeOut(BaseModel):
    id: str
    job_id: str
    filename: str
    candidate_name: str
    email: str
    phone: str
    created_at: datetime
    class Config: from_attributes = True

# Results
class ResultUpdate(BaseModel):
    status: Optional[str] = None
    notes: Optional[str] = None
    tags: Optional[List[str]] = None

class ScoreBreakdown(BaseModel):
    semantic_similarity: float
    skill_match: float
    experience_alignment: float
    education_alignment: float
    formatting_clarity: float
    total: float

class ResultOut(BaseModel):
    id: str
    job_id: str
    resume_id: str
    score: float
    confidence: float
    seniority: str
    breakdown: Dict[str, Any]
    evidence: List[Dict[str, Any]]
    matched_skills: List[str]
    missing_skills: List[str]
    nice_to_have_found: List[str]
    red_flags: List[str] = []
    recommendations: List[str] = []
    interview_questions: List[Dict[str, str]] = []
    project_evaluations: List[Dict[str, Any]] = []
    fraud_flags: List[Dict[str, str]] = []
    strength_tags: List[str] = []
    explanation: str = ""
    status: str
    notes: str
    tags: List[str]
    created_at: datetime
    candidate_name: Optional[str] = ""
    candidate_email: Optional[str] = ""
    candidate_id: Optional[str] = ""
    filename: Optional[str] = ""
    class Config: from_attributes = True

# Analytics
class JobAnalytics(BaseModel):
    total_candidates: int
    avg_score: float
    score_distribution: Dict[str, int]
    top_missing_skills: List[Dict[str, Any]]
    shortlisted: int
    rejected: int
    hold: int
    pending: int

class AdminAnalytics(BaseModel):
    total_jobs: int
    total_resumes: int
    total_screenings: int
    avg_score: float
    recruiter_activity: List[Dict[str, Any]]

# Candidate Portal
class CandidateProfileOut(BaseModel):
    id: str
    user_id: str
    filename: str
    extracted_skills: List[str]
    contact_info: Dict[str, Any]
    overall_score: float
    seniority: str = ""
    breakdown: Dict[str, Any] = {}
    strength_tags: List[str] = []
    explanation: str = ""
    created_at: datetime
    updated_at: Optional[datetime] = None
    class Config: from_attributes = True

class ApplicationOut(BaseModel):
    id: str
    candidate_id: str
    job_id: str
    score: float
    match_percent: float
    matched_skills: List[str]
    missing_skills: List[str]
    status: str
    breakdown: Dict = {}
    recommendations: List[str] = []
    strength_tags: List[str] = []
    explanation: str = ""
    project_evaluations: List[Dict[str, Any]] = []
    fraud_flags: List[Dict[str, str]] = []
    applied_at: datetime
    job_title: Optional[str] = ""
    company: Optional[str] = ""
    class Config: from_attributes = True

class JobPublicOut(BaseModel):
    id: str
    title: str
    company: str
    jd_text: str
    required_skills: List[str]
    nice_to_have_skills: List[str]
    min_years_exp: int
    created_at: datetime
    application_count: Optional[int] = 0
    match_percent: Optional[float] = None
    class Config: from_attributes = True

class SkillSuggestion(BaseModel):
    skill: str
    demand_count: int
    priority: str  # high/medium/low

class ResumeTip(BaseModel):
    category: str  # formatting/content/skills/structure
    tip: str
    impact: str  # high/medium/low

class JobRecommendation(BaseModel):
    job_id: str
    title: str
    company: str
    match_percent: float
    matched_skills: List[str]
    missing_skills: List[str]

