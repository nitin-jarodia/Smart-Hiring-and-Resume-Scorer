"""Seed the database with sample data for testing and wipe old data."""
import sys
import os
import shutil
from datetime import datetime, timedelta

sys.path.insert(0, ".")

from app.database import SessionLocal, engine
from app.models.domain import Base, User, Job, Resume, Result, CandidateProfile, Application, Interview
from app.auth.security import get_password_hash
from app.ai.parser import extract_text, extract_contact_info, detect_sections
from app.ai.scorer import score_resume

# 1. Wipe the old database and uploads folder
print("Resetting database...")
Base.metadata.drop_all(bind=engine)
if os.path.exists("resume_screener.db"):
    try:
        os.remove("resume_screener.db")
    except:
        pass

if os.path.exists("uploads"):
    shutil.rmtree("uploads", ignore_errors=True)

Base.metadata.create_all(bind=engine)
db = SessionLocal()

print("Creating sample users...")
# 2. Create users (Recruiters, Admin, Candidate)
admin = User(email="admin@screener.dev", hashed_password=get_password_hash("admin123"), full_name="Admin User", role="admin")
db.add(admin)

recruiter = User(email="recruiter@screener.dev", hashed_password=get_password_hash("recruiter123"), full_name="Sarah Recruiter", role="recruiter")
db.add(recruiter)

candidate_user = User(email="candidate@example.com", hashed_password=get_password_hash("password123"), full_name="John Candidate", role="candidate")
db.add(candidate_user)

db.commit()
db.refresh(admin)
db.refresh(recruiter)
db.refresh(candidate_user)

print("Creating jobs...")
# 3. Read JD
jd_path = "samples/sample_jd_senior_backend.txt"
with open(jd_path) as f:
    jd_text = f.read()

# Create job
job = Job(
    created_by=recruiter.id,
    title="Senior Backend Engineer - Platform Team",
    company="Acme Tech",
    jd_text=jd_text,
    required_skills=["python", "postgresql", "redis", "aws", "docker", "kubernetes", "microservices", "rest api", "ci/cd", "git"],
    nice_to_have_skills=["golang", "terraform", "graphql", "kafka"],
    min_years_exp=5,
)
db.add(job)

job2 = Job(
    created_by=admin.id,
    title="Frontend Developer - React",
    company="Tech Corp",
    jd_text="Looking for a React developer with at least 3 years of experience. Must know Typescript, Tailwind CSS, and Next.js.",
    required_skills=["react", "typescript", "tailwind css", "next.js", "javascript", "html", "css", "git"],
    nice_to_have_skills=["graphql", "jest", "cypress", "node.js"],
    min_years_exp=3,
)
db.add(job2)
db.commit()
db.refresh(job)
db.refresh(job2)


print("Creating candidate profiles...")
# 4. Set up Candidate Profile for Candidate User
os.makedirs("uploads", exist_ok=True)
candidate_resume_path = "samples/resumes/emma_patel_junior.txt"
candidate_dest = "uploads/john_candidate_resume.txt"
shutil.copy(candidate_resume_path, candidate_dest)
candidate_text = extract_text(candidate_resume_path)
candidate_contact = extract_contact_info(candidate_text)
candidate_sections = detect_sections(candidate_text)

profile = CandidateProfile(
    user_id=candidate_user.id,
    resume_path=candidate_dest,
    filename="john_candidate_resume.txt",
    extracted_text=candidate_text,
    extracted_skills=["python", "javascript", "react", "html", "css"],
    contact_info=candidate_contact,
    sections=candidate_sections,
    overall_score=0.0
)
db.add(profile)
db.commit()
db.refresh(profile)

# 5. Create Candidate's application for Market Trends features & UI
print("Scoring candidate application...")
app_result_data = score_resume(job2.jd_text, candidate_text, job2.required_skills)
app = Application(
    candidate_id=profile.id,
    job_id=job2.id,
    score=app_result_data["score"],
    match_percent=75.0, # Dummy calc
    matched_skills=app_result_data.get("matched_skills", []),
    missing_skills=app_result_data.get("missing_skills", []),
    status="shortlisted",
    breakdown=app_result_data.get("breakdown", {}),
    recommendations=app_result_data.get("recommendations", []),
    project_evaluations=app_result_data.get("project_evaluations", [])
)
db.add(app)
db.commit()
db.refresh(app)

print("Scheduling candidate interview...")
# Create a sample Interview for that candidate
interview_time = datetime.now() + timedelta(days=2)
interview = Interview(
    result_id=app.id,
    scheduled_at=interview_time,
    duration_minutes=60,
    meeting_link="https://meet.google.com/abc-defg-hij",
    notes="First round technical interview focusing on React fundamentals.",
    status="scheduled"
)
db.add(interview)
db.commit()


print("Seeding diverse recruiter resumes...")
# 6. Seed Recruiter Resumes directly into the Job
resume_files = [
    "samples/resumes/alice_chen_senior_backend.txt",
    "samples/resumes/bob_martinez_mid_backend.txt", 
    "samples/resumes/carol_johnson_frontend_mismatch.txt",
    "samples/resumes/david_kim_overqualified.txt",
]

for filepath in resume_files:
    filename = os.path.basename(filepath)
    dest = f"uploads/{filename}"
    shutil.copy(filepath, dest)
    
    text = extract_text(filepath)
    contact = extract_contact_info(text)
    sections = detect_sections(text)
    
    resume = Resume(
        job_id=job.id,
        filename=filename,
        file_path=dest,
        extracted_text=text,
        candidate_name=contact.get("name", "Unknown"),
        email=contact.get("email", ""),
        phone=contact.get("phone", ""),
        sections=sections,
    )
    db.add(resume)
    db.commit()
    db.refresh(resume)
    
    # Score it heavily to test the Fraud / AI flags
    result_data = score_resume(jd_text, text, job.required_skills)
    result = Result(
        job_id=job.id,
        resume_id=resume.id,
        score=result_data["score"],
        confidence=result_data["confidence"],
        seniority=result_data["seniority"],
        breakdown=result_data["breakdown"],
        evidence=result_data["evidence"],
        matched_skills=result_data["matched_skills"],
        missing_skills=result_data["missing_skills"],
        nice_to_have_found=result_data.get("nice_to_have_found", []),
        red_flags=result_data.get("red_flags", []),
        fraud_flags=result_data.get("fraud_flags", []),
        project_evaluations=result_data.get("project_evaluations", []),
        recommendations=result_data.get("recommendations", []),
        interview_questions=result_data.get("interview_questions", []),
        explanation=result_data.get("explanation", ""),
        status="pending",
    )
    db.add(result)
    db.commit()
    print(f"Scored {filename}: {result_data['score']:.1f}")

db.close()
print("\nReset & Seed complete! Login with:")
print("  admin@screener.dev / admin123")
print("  recruiter@screener.dev / recruiter123")
print("  candidate@example.com / password123")

