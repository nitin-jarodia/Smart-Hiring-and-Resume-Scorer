from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..models.domain import Job, Application
from ..models.schemas import JobCreate, JobOut
from ..auth.security import require_recruiter
from ..ai.skill_extractor import extract_skills_from_text, extract_required_skills_from_jd

router = APIRouter(prefix="/jobs", tags=["jobs"])

@router.post("", response_model=JobOut)
def create_job(data: JobCreate, db: Session = Depends(get_db), current_user=Depends(require_recruiter)):
    # Auto-extract skills from JD if not provided
    required_skills = data.required_skills
    nice_to_have = data.nice_to_have_skills
    
    if not required_skills:
        required_skills, nice_to_have = extract_required_skills_from_jd(data.jd_text)
    
    job = Job(
        created_by=current_user.id,
        title=data.title,
        company=data.company or "",
        jd_text=data.jd_text,
        required_skills=required_skills,
        nice_to_have_skills=nice_to_have,
        min_years_exp=data.min_years_exp or 0,
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    
    result = JobOut.model_validate(job)
    result.resume_count = 0
    return result

@router.get("", response_model=List[JobOut])
def list_jobs(db: Session = Depends(get_db), current_user=Depends(require_recruiter)):
    if current_user.role == "admin":
        jobs = db.query(Job).order_by(Job.created_at.desc()).all()
    else:
        jobs = db.query(Job).filter(Job.created_by == current_user.id).order_by(Job.created_at.desc()).all()
    
    results = []
    for job in jobs:
        out = JobOut.model_validate(job)
        out.resume_count = len(job.resumes)
        results.append(out)
    return results

@router.get("/public")
def list_public_jobs(db: Session = Depends(get_db)):
    """List all jobs publicly — no authentication required."""
    jobs = db.query(Job).order_by(Job.created_at.desc()).all()
    result = []
    for job in jobs:
        app_count = db.query(Application).filter(Application.job_id == job.id).count()
        result.append({
            "id": job.id,
            "title": job.title,
            "company": job.company,
            "jd_text": job.jd_text,
            "required_skills": job.required_skills,
            "nice_to_have_skills": job.nice_to_have_skills,
            "min_years_exp": job.min_years_exp,
            "created_at": job.created_at,
            "application_count": app_count,
        })
    return result

@router.get("/{job_id}", response_model=JobOut)
def get_job(job_id: str, db: Session = Depends(get_db), current_user=Depends(require_recruiter)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    out = JobOut.model_validate(job)
    out.resume_count = len(job.resumes)
    return out

@router.delete("/{job_id}")
def delete_job(job_id: str, db: Session = Depends(get_db), current_user=Depends(require_recruiter)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.created_by != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    db.delete(job)
    db.commit()
    return {"message": "Job deleted"}
