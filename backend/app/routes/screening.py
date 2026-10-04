from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from ..database import get_db
from ..models.domain import Job, Resume, Result, Application
from ..models.schemas import ResultOut, ResultUpdate
from ..auth.security import require_recruiter
from ..auth.ownership import get_job_for_user
from ..ai.scorer import score_resume
from ..ai.rag import grounded_explanation, citation_evidence, ensure_indexed, retrieve
from ..ai.llm import answer_from_chunks
from pydantic import BaseModel, Field
import logging
logger = logging.getLogger(__name__)

router = APIRouter(tags=["screening"])


def _app_to_result_out(app: Application) -> ResultOut:
    """Convert a candidate Application to a ResultOut schema."""
    d = {
        "id": app.id,
        "job_id": app.job_id,
        "resume_id": app.candidate_id,  # mapped for typing compat
        "score": app.score,
        "confidence": 0.0,
        "seniority": app.seniority or "Unknown",
        "breakdown": app.breakdown or {},
        "evidence": [],
        "matched_skills": app.matched_skills or [],
        "missing_skills": app.missing_skills or [],
        "nice_to_have_found": [],
        "red_flags": [],
        "recommendations": app.recommendations or [],
        "interview_questions": [],
        "project_evaluations": app.project_evaluations or [],
        "fraud_flags": app.fraud_flags or [],
        "strength_tags": app.strength_tags or [],
        "candidate_id": app.candidate_id,
        "status": app.status,
        "notes": "",
        "tags": [],
        "created_at": app.applied_at,
    }
    item = ResultOut(**d)
    if app.candidate:
        item.candidate_name = app.candidate.user.full_name if app.candidate.user else ""
        item.candidate_email = app.candidate.user.email if app.candidate.user else ""
        item.filename = app.candidate.filename
    return item


def run_scoring_sync(job_id: str, db: Session):
    """Run scoring for all resumes in a job synchronously.
    NOTE: This blocks the event loop. For large batches, migrate to Celery/Redis.
    """
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        return

    resumes = db.query(Resume).filter(Resume.job_id == job_id).all()
    jd_skills = job.required_skills or []

    for resume in resumes:
        try:
            # Delete existing result
            existing = db.query(Result).filter(Result.resume_id == resume.id).first()
            if existing:
                db.delete(existing)
                db.commit()

            if not resume.extracted_text or len(resume.extracted_text.strip()) < 50:
                logger.warning(f"Resume {resume.id} has insufficient text for scoring")
                result_data = {
                    "score": 0, "confidence": 0, "seniority": "Unknown",
                    "breakdown": {}, "evidence": [], "matched_skills": [],
                    "missing_skills": jd_skills, "nice_to_have_found": [],
                    "red_flags": ["Could not extract text from resume"],
                    "recommendations": ["Please re-upload the resume in a supported format (PDF, DOCX, TXT)"],
                    "interview_questions": [],
                    "explanation": "Unable to process this resume. Text extraction failed.",
                    "fraud_flags": [], "project_evaluations": [],
                }
            else:
                result_data = score_resume(job.jd_text, resume.extracted_text, jd_skills)
                try:
                    grounded = grounded_explanation(
                        db,
                        job.jd_text,
                        resume.extracted_text,
                        resume_id=resume.id,
                    )
                    # Keep the template narrative when no model is configured; the
                    # retrieved passages are still attached as citations.
                    if grounded.get("used_llm") and grounded.get("answer"):
                        result_data["explanation"] = grounded["answer"]
                    result_data["evidence"] = list(result_data.get("evidence") or []) + citation_evidence(
                        grounded.get("citations") or []
                    )
                except Exception as e:
                    logger.error(f"RAG explanation failed for resume {resume.id}: {e}")

            result = Result(
                job_id=job_id,
                resume_id=resume.id,
                score=result_data["score"],
                confidence=result_data["confidence"],
                seniority=result_data["seniority"],
                breakdown=result_data["breakdown"],
                evidence=result_data["evidence"],
                matched_skills=result_data["matched_skills"],
                missing_skills=result_data["missing_skills"],
                nice_to_have_found=result_data.get("nice_to_have_found", []),
                red_flags=result_data["red_flags"],
                fraud_flags=result_data.get("fraud_flags", []),
                recommendations=result_data["recommendations"],
                interview_questions=result_data["interview_questions"],
                project_evaluations=result_data.get("project_evaluations", []),
                explanation=result_data["explanation"],
                status="pending",
            )
            db.add(result)
            db.commit()
            logger.info(f"Scored resume {resume.id}: {result_data['score']}")
        except Exception as e:
            logger.error(f"Error scoring resume {resume.id}: {e}")
            db.rollback()


@router.post("/jobs/{job_id}/screen")
async def screen_resumes(
    job_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user=Depends(require_recruiter),
):
    get_job_for_user(db, job_id, current_user)

    resume_count = db.query(Resume).filter(Resume.job_id == job_id).count()
    if resume_count == 0:
        raise HTTPException(status_code=400, detail="No resumes uploaded for this job")

    run_scoring_sync(job_id, db)
    return {"message": f"Screening complete for {resume_count} resumes", "job_id": job_id}


@router.get("/jobs/{job_id}/results", response_model=List[ResultOut])
def get_results(
    job_id: str,
    status: Optional[str] = None,
    min_score: Optional[float] = None,
    db: Session = Depends(get_db),
    current_user=Depends(require_recruiter),
):
    get_job_for_user(db, job_id, current_user)

    # 1. Recruiter-uploaded resumes
    query = db.query(Result).filter(Result.job_id == job_id)
    if status:
        query = query.filter(Result.status == status)
    if min_score is not None:
        query = query.filter(Result.score >= min_score)

    out = []
    for r in query.all():
        item = ResultOut.model_validate(r)
        if r.resume:
            item.candidate_name = r.resume.candidate_name
            item.candidate_email = r.resume.email
            item.filename = r.resume.filename
        out.append(item)

    # 2. Candidate self-applications
    app_query = db.query(Application).filter(Application.job_id == job_id)
    if status:
        app_query = app_query.filter(Application.status == status)
    if min_score is not None:
        app_query = app_query.filter(Application.score >= min_score)

    for app in app_query.all():
        out.append(_app_to_result_out(app))

    out.sort(key=lambda x: x.score, reverse=True)
    return out


@router.patch("/results/{result_id}")
def update_result(
    result_id: str,
    data: ResultUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(require_recruiter),
):
    # Try recruiter-uploaded Result first
    result = db.query(Result).filter(Result.id == result_id).first()
    if result:
        get_job_for_user(db, result.job_id, current_user)
        if data.status is not None:
            result.status = data.status
        if data.notes is not None:
            result.notes = data.notes
        if data.tags is not None:
            result.tags = data.tags
        db.commit()
        db.refresh(result)
        item = ResultOut.model_validate(result)
        if result.resume:
            item.candidate_name = result.resume.candidate_name
            item.candidate_email = result.resume.email
            item.filename = result.resume.filename
        return item

    # Try candidate Application
    app = db.query(Application).filter(Application.id == result_id).first()
    if app:
        get_job_for_user(db, app.job_id, current_user)
        if data.status is not None:
            app.status = data.status
        db.commit()
        db.refresh(app)
        return _app_to_result_out(app)

    raise HTTPException(status_code=404, detail="Result or Application not found")


class AskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=500)


@router.post("/results/{result_id}/ask")
def ask_result(
    result_id: str,
    body: AskRequest,
    db: Session = Depends(get_db),
    current_user=Depends(require_recruiter),
):
    question = body.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question is required")

    result = db.query(Result).filter(Result.id == result_id).first()
    if result:
        get_job_for_user(db, result.job_id, current_user)
        resume = result.resume
        text = resume.extracted_text if resume else ""
        if not text or not text.strip():
            raise HTTPException(status_code=400, detail="No resume text to search")
        ensure_indexed(db, text, resume_id=resume.id)
        hits = retrieve(db, question, resume_id=resume.id, top_k=5)
        return answer_from_chunks(question, hits)

    app = db.query(Application).filter(Application.id == result_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Result or Application not found")

    get_job_for_user(db, app.job_id, current_user)
    profile = app.candidate
    text = profile.extracted_text if profile else ""
    if not text or not text.strip():
        raise HTTPException(status_code=400, detail="No resume text to search")
    ensure_indexed(db, text, candidate_id=profile.id)
    hits = retrieve(db, question, candidate_id=profile.id, top_k=5)
    return answer_from_chunks(question, hits)
