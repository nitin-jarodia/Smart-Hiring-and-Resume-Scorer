from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from collections import Counter
from ..database import get_db
from ..models.domain import Job, Resume, Result, User

from ..auth.security import get_current_user, require_admin, require_recruiter

router = APIRouter(prefix="/analytics", tags=["analytics"])

@router.get("/jobs/{job_id}")
def job_analytics(job_id: str, db: Session = Depends(get_db), current_user: User = Depends(require_recruiter)):
    from ..models.domain import Application
    results = db.query(Result).filter(Result.job_id == job_id).all()
    apps = db.query(Application).filter(Application.job_id == job_id).all()

    if not results and not apps:
        return {"total_candidates": 0, "avg_score": 0, "score_distribution": {},
                "top_missing_skills": [], "shortlisted": 0, "rejected": 0, "hold": 0, "pending": 0}

    all_scores = [r.score for r in results] + [a.score for a in apps]
    avg_score = sum(all_scores) / len(all_scores) if all_scores else 0

    # Score distribution buckets
    distribution = {"0-20": 0, "21-40": 0, "41-60": 0, "61-80": 0, "81-100": 0}
    for s in all_scores:
        if s <= 20: distribution["0-20"] += 1
        elif s <= 40: distribution["21-40"] += 1
        elif s <= 60: distribution["41-60"] += 1
        elif s <= 80: distribution["61-80"] += 1
        else: distribution["81-100"] += 1

    # Missing skills aggregation
    all_missing = []
    for r in results:
        all_missing.extend(r.missing_skills or [])
    for a in apps:
        all_missing.extend(a.missing_skills or [])
    missing_counter = Counter(all_missing).most_common(10)
    top_missing = [{"skill": k, "count": v} for k, v in missing_counter]

    all_statuses = [r.status for r in results] + [a.status for a in apps]
    status_counts = Counter(all_statuses)

    return {
        "total_candidates": len(results) + len(apps),
        "avg_score": round(avg_score, 1),
        "score_distribution": distribution,
        "top_missing_skills": top_missing,
        "shortlisted": status_counts.get("shortlisted", 0),
        "rejected": status_counts.get("rejected", 0),
        "hold": status_counts.get("hold", 0),
        "pending": status_counts.get("pending", 0),
    }

@router.get("/admin")
def admin_analytics(db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    total_jobs = db.query(Job).count()
    total_resumes = db.query(Resume).count()
    total_results = db.query(Result).count()
    
    all_scores = [r.score for r in db.query(Result).all()]
    avg_score = sum(all_scores) / len(all_scores) if all_scores else 0
    
    # Recruiter activity
    recruiters = db.query(User).filter(User.role == "recruiter").all()
    activity = []
    for rec in recruiters:
        job_count = db.query(Job).filter(Job.created_by == rec.id).count()
        activity.append({
            "recruiter": rec.email,
            "name": rec.full_name,
            "jobs_created": job_count,
        })
    
    return {
        "total_jobs": total_jobs,
        "total_resumes": total_resumes,
        "total_screenings": total_results,
        "avg_score": round(avg_score, 1),
        "recruiter_activity": activity,
    }
