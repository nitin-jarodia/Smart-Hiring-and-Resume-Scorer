from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
from collections import Counter
import os, shutil, logging

logger = logging.getLogger(__name__)

from ..database import get_db
from ..models.domain import User, Job, CandidateProfile, Application
from ..models.schemas import (
    CandidateProfileOut, ApplicationOut, JobPublicOut,
    SkillSuggestion, ResumeTip, JobRecommendation,
)
from ..auth.security import require_candidate
from ..ai.parser import extract_text, extract_contact_info, detect_sections
from ..ai.skill_extractor import extract_skills_from_text
from ..ai.scorer import score_resume, generate_resume_tips, analyze_general_profile
from ..ai.market_trends import get_market_trend_recommendations
from ..ai.vector_search import update_candidate_embedding
from ..config import settings

router = APIRouter(tags=["candidate"])


# ─── Profile ──────────────────────────────────────────────────────────────────

@router.post("/candidate/profile")
async def upload_resume_profile(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_candidate),
):
    """Upload resume and create/update candidate profile."""
    # Validate file type
    allowed = ('.pdf', '.docx', '.txt')
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in allowed:
        raise HTTPException(status_code=400, detail=f"File type {ext} not supported. Use PDF, DOCX, or TXT.")

    # Save file
    upload_dir = getattr(settings, "UPLOAD_DIR", "./uploads")
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, f"candidate_{current_user.id}{ext}")
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)

    # Extract text and info
    extracted_text = extract_text(file_path)
    contact = extract_contact_info(extracted_text)
    sections = detect_sections(extracted_text)
    skills = extract_skills_from_text(extracted_text)

    # General Analysis
    analysis = analyze_general_profile(extracted_text)

    # Create or update profile
    profile = db.query(CandidateProfile).filter(
        CandidateProfile.user_id == current_user.id
    ).first()

    if profile:
        profile.resume_path = file_path
        profile.filename = file.filename or ""
        profile.extracted_text = extracted_text
        profile.extracted_skills = skills
        profile.contact_info = contact
        profile.sections = sections
        profile.overall_score = analysis["score"]
        profile.seniority = analysis["seniority"]
        profile.breakdown = analysis["breakdown"]
        profile.strength_tags = analysis["strength_tags"]
        profile.explanation = analysis["explanation"]
    else:
        profile = CandidateProfile(
            user_id=current_user.id,
            resume_path=file_path,
            filename=file.filename or "",
            extracted_text=extracted_text,
            extracted_skills=skills,
            contact_info=contact,
            sections=sections,
            overall_score=analysis["score"],
            seniority=analysis["seniority"],
            breakdown=analysis["breakdown"],
            strength_tags=analysis["strength_tags"],
            explanation=analysis["explanation"],
        )
        db.add(profile)

    db.commit()
    db.refresh(profile)

    # Automatically generate semantic embedding in background
    if profile.extracted_text:
        background_tasks.add_task(update_candidate_embedding, profile.id, profile.extracted_text)

    return {
        "message": "Resume uploaded successfully",
        "profile_id": profile.id,
        "extracted_skills": skills,
        "contact_info": contact,
        "filename": profile.filename,
    }


@router.get("/candidate/profile")
def get_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_candidate),
):
    """Get candidate's own profile with resume info."""
    profile = db.query(CandidateProfile).filter(
        CandidateProfile.user_id == current_user.id
    ).first()

    if not profile:
        return {"has_profile": False, "message": "No resume uploaded yet"}

    return {
        "has_profile": True,
        "id": profile.id,
        "filename": profile.filename,
        "extracted_skills": profile.extracted_skills,
        "contact_info": profile.contact_info,
        "sections": profile.sections,
        "overall_score": profile.overall_score,
        "seniority": profile.seniority,
        "breakdown": profile.breakdown,
        "strength_tags": profile.strength_tags,
        "explanation": profile.explanation,
        "created_at": profile.created_at,
        "updated_at": profile.updated_at,
    }


# ─── Apply ────────────────────────────────────────────────────────────────────

@router.post("/candidate/apply/{job_id}")
def apply_to_job(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_candidate),
):
    """Apply to a job — auto-scores resume against JD."""
    profile = db.query(CandidateProfile).filter(
        CandidateProfile.user_id == current_user.id
    ).first()
    if not profile or not profile.extracted_text:
        raise HTTPException(status_code=400, detail="Please upload your resume first")

    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # Check if already applied
    existing = db.query(Application).filter(
        Application.candidate_id == profile.id,
        Application.job_id == job_id,
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Already applied to this job")

    # AI Score resume against job
    try:
        result = score_resume(job.jd_text, profile.extracted_text, job.required_skills or [])
    except Exception as e:
        logger.error(f"Scoring error: {e}")
        result = {
            "score": 0, "breakdown": {}, "matched_skills": [],
            "missing_skills": job.required_skills or [],
            "recommendations": ["Unable to score. Please re-upload your resume."],
        }

    # Calculate match percent
    required = set(s.lower() for s in (job.required_skills or []))
    matched = set(s.lower() for s in result.get("matched_skills", []))
    match_pct = (len(matched & required) / len(required) * 100) if required else 0

    app = Application(
        candidate_id=profile.id,
        job_id=job_id,
        score=result["score"],
        match_percent=round(match_pct, 1),
        matched_skills=result.get("matched_skills", []),
        missing_skills=result.get("missing_skills", []),
        breakdown=result.get("breakdown", {}),
        recommendations=result.get("recommendations", []),
        project_evaluations=result.get("project_evaluations", []),
        fraud_flags=result.get("fraud_flags", []),
        strength_tags=result.get("strength_tags", []),
        explanation=result.get("explanation", ""),
        seniority=result.get("seniority", "Unknown"),
        status="pending",
    )
    db.add(app)

    # Update overall score as average of all applications
    all_apps = db.query(Application).filter(Application.candidate_id == profile.id).all()
    scores = [a.score for a in all_apps] + [result["score"]]
    profile.overall_score = round(sum(scores) / len(scores), 1)

    db.commit()
    db.refresh(app)

    return {
        "message": f"Applied to {job.title} successfully!",
        "application_id": app.id,
        "score": app.score,
        "match_percent": app.match_percent,
        "matched_skills": app.matched_skills,
        "missing_skills": app.missing_skills,
    }


# ─── Applications ─────────────────────────────────────────────────────────────

@router.get("/candidate/applications")
def get_applications(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_candidate),
):
    """List candidate's job applications with statuses."""
    profile = db.query(CandidateProfile).filter(
        CandidateProfile.user_id == current_user.id
    ).first()
    if not profile:
        return []

    apps = db.query(Application).filter(
        Application.candidate_id == profile.id
    ).order_by(Application.applied_at.desc()).all()

    result = []
    for app in apps:
        job = db.query(Job).filter(Job.id == app.job_id).first()
        result.append({
            "id": app.id,
            "job_id": app.job_id,
            "job_title": job.title if job else "Unknown",
            "company": job.company if job else "",
            "score": app.score,
            "match_percent": app.match_percent,
            "matched_skills": app.matched_skills,
            "missing_skills": app.missing_skills,
            "status": app.status,
            "breakdown": app.breakdown,
            "recommendations": app.recommendations,
            "project_evaluations": app.project_evaluations,
            "fraud_flags": app.fraud_flags,
            "strength_tags": app.strength_tags,
            "explanation": app.explanation,
            "seniority": app.seniority,
            "applied_at": app.applied_at,
        })
    return result


# ─── Recommendations ──────────────────────────────────────────────────────────

@router.get("/candidate/recommendations")
def get_recommendations(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_candidate),
):
    """AI-ranked job recommendations based on resume match."""
    profile = db.query(CandidateProfile).filter(
        CandidateProfile.user_id == current_user.id
    ).first()
    if not profile or not profile.extracted_text:
        return []

    # Get all jobs
    jobs = db.query(Job).all()
    if not jobs:
        return []

    # Already-applied job IDs
    applied_ids = set()
    if profile:
        apps = db.query(Application).filter(Application.candidate_id == profile.id).all()
        applied_ids = {a.job_id for a in apps}

    recommendations = []
    for job in jobs:
        jd_skills = set(s.lower() for s in (job.required_skills or []))
        candidate_skills = set(s.lower() for s in (profile.extracted_skills or []))
        matched = list(jd_skills & candidate_skills)
        missing = list(jd_skills - candidate_skills)
        match_pct = (len(matched) / len(jd_skills) * 100) if jd_skills else 0

        recommendations.append({
            "job_id": job.id,
            "title": job.title,
            "company": job.company,
            "match_percent": round(match_pct, 1),
            "matched_skills": matched,
            "missing_skills": missing,
            "already_applied": job.id in applied_ids,
        })

    # Sort by match percent descending
    recommendations.sort(key=lambda x: x["match_percent"], reverse=True)
    return recommendations


# ─── Skill Suggestions ────────────────────────────────────────────────────────

@router.get("/candidate/skills-suggestions")
def get_skill_suggestions(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_candidate),
):
    """Top skills to learn strictly based on candidate's applied jobs or market demand."""
    profile = db.query(CandidateProfile).filter(
        CandidateProfile.user_id == current_user.id
    ).first()

    candidate_skills = set(s.strip().lower() for s in (profile.extracted_skills if profile else []))

    if not profile:
        # No resume uploaded — return pure market trends
        market_trends = get_market_trend_recommendations([])
        return market_trends[:15]

    # Focus deeply on jobs the candidate has shown interest in
    apps = db.query(Application).filter(Application.candidate_id == profile.id).all()

    if apps:
        job_ids = [a.job_id for a in apps]
        jobs_to_analyze = db.query(Job).filter(Job.id.in_(job_ids)).all()
    else:
        # Fallback to all jobs if no applications yet
        jobs_to_analyze = db.query(Job).all()

    # Aggregate only skills that are strictly missing
    skill_demand: dict = {}
    for job in jobs_to_analyze:
        for skill in (job.required_skills or []):
            sl = skill.strip().lower()
            if sl and sl not in candidate_skills:
                if sl not in skill_demand:
                    skill_demand[sl] = {"count": 1, "display": skill.strip()}
                else:
                    skill_demand[sl]["count"] += 1

    # Format output
    suggestions = []
    # Dynamic threshold based on sample size
    high_threshold = max(2, len(jobs_to_analyze) // 2) 
    
    for sl, data in sorted(skill_demand.items(), key=lambda x: -x[1]["count"]):
        count = data["count"]
        priority = "high" if count >= high_threshold else "medium" if count >= 2 else "low"
        
        suggestions.append({
            "skill": data["display"],
            "demand_count": count,
            "priority": priority,
        })

    # Add Market Trends
    market_trends = get_market_trend_recommendations(list(candidate_skills))
    
    # Avoid duplicates if a market trend is already in the organic suggestions
    existing_skills = {s["skill"].replace(" 🚀", "").lower() for s in suggestions}
    
    for mt in market_trends:
        base_skill = mt["skill"].replace(" 🚀", "").lower()
        if base_skill not in existing_skills:
            suggestions.append(mt)
            
    # Sort again to ensure high priority/demand items (including market trends) are at the top
    suggestions.sort(key=lambda x: (-x.get("demand_count", 0)))
            
    return suggestions[:15]


# ─── Resume Tips ──────────────────────────────────────────────────────────────

@router.get("/candidate/resume-tips")
def get_resume_tips(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_candidate),
):
    """AI-generated resume improvement suggestions."""
    profile = db.query(CandidateProfile).filter(
        CandidateProfile.user_id == current_user.id
    ).first()
    if not profile or not profile.extracted_text:
        return [{"category": "upload", "tip": "Upload your resume to get personalized tips", "impact": "high"}]

    return generate_resume_tips(profile.extracted_text, profile.sections or {}, profile.extracted_skills or [])

