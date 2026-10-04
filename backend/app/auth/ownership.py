"""Shared authorization helpers for job-scoped resources."""
from typing import Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from ..models.domain import Application, Job, Resume, Result, User


def get_job_for_user(db: Session, job_id: str, user: User) -> Job:
    """Return the job only when the caller created it, or is an admin."""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if user.role != "admin" and job.created_by != user.id:
        raise HTTPException(status_code=403, detail="Not authorized for this job")
    return job


def get_resume_for_user(db: Session, resume_id: str, user: User) -> Resume:
    """Return the resume only when the caller owns its job, or is an admin."""
    resume = db.query(Resume).filter(Resume.id == resume_id).first()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    get_job_for_user(db, resume.job_id, user)
    return resume


def find_job_id_for_result(db: Session, result_id: str) -> Optional[str]:
    """Resolve a screening Result id or a candidate Application id to its job id."""
    result = db.query(Result).filter(Result.id == result_id).first()
    if result:
        return result.job_id
    application = db.query(Application).filter(Application.id == result_id).first()
    if application:
        return application.job_id
    return None


def candidate_owns_result(db: Session, result_id: str, user: User) -> bool:
    """True when the caller is the candidate behind this application."""
    if user.role != "candidate" or not user.candidate_profile:
        return False
    return db.query(Application).filter(
        Application.id == result_id,
        Application.candidate_id == user.candidate_profile.id,
    ).first() is not None


def require_result_access(db: Session, result_id: str, user: User) -> None:
    """Allow the owning recruiter, an admin, or the candidate the record belongs to."""
    if candidate_owns_result(db, result_id, user):
        return
    job_id = find_job_id_for_result(db, result_id)
    if not job_id:
        raise HTTPException(status_code=404, detail="Result or Application not found")
    get_job_for_user(db, job_id, user)


def require_candidate_profile_access(db: Session, candidate_id: str, user: User) -> None:
    """Allow an admin, the candidate themselves, or a recruiter they applied to."""
    if user.role == "admin":
        return
    if user.role == "candidate":
        profile = user.candidate_profile
        if profile and profile.id == candidate_id:
            return
        raise HTTPException(status_code=403, detail="Not authorized for this candidate")

    applied = db.query(Application).join(Job, Application.job_id == Job.id).filter(
        Application.candidate_id == candidate_id,
        Job.created_by == user.id,
    ).first()
    if not applied:
        raise HTTPException(status_code=403, detail="Not authorized for this candidate")
