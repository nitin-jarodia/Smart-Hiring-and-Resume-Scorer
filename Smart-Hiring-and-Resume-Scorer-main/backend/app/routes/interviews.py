from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)

from ..database import get_db
from ..models.domain import User, Application, Interview, Job, Result
from ..auth.security import get_current_user, require_recruiter

router = APIRouter(prefix="/interviews", tags=["Interviews"])

class InterviewCreate(BaseModel):
    result_id: str
    scheduled_at: datetime
    duration_minutes: int = 60
    meeting_link: str = ""
    notes: str = ""

class InterviewUpdate(BaseModel):
    scheduled_at: Optional[datetime] = None
    duration_minutes: Optional[int] = None
    meeting_link: Optional[str] = None
    notes: Optional[str] = None
    status: Optional[str] = None

class InterviewOut(BaseModel):
    id: str
    result_id: str
    scheduled_at: datetime
    duration_minutes: int
    meeting_link: str
    notes: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True

@router.post("", response_model=InterviewOut)
def schedule_interview(data: InterviewCreate, db: Session = Depends(get_db), user: User = Depends(require_recruiter)):
    # Check if result_id is an Application or a Result
    record = db.query(Result).filter(Result.id == data.result_id).first()
    if not record:
        record = db.query(Application).filter(Application.id == data.result_id).first()
        
    if not record:
        raise HTTPException(status_code=404, detail="Application or Result not found")
        
    interview = Interview(**data.model_dump())
    db.add(interview)
    
    # Update status
    record.status = "interviewed"
    
    db.commit()
    db.refresh(interview)
    return interview

@router.get("/result/{res_id}", response_model=List[InterviewOut])
def get_interviews_for_result(res_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(Interview).filter(Interview.result_id == res_id).order_by(Interview.scheduled_at).all()

@router.get("/my-interviews", response_model=List[InterviewOut])
def get_my_interviews(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if user.role == "candidate":
        if not user.candidate_profile:
            return []
        apps = [app.id for app in user.candidate_profile.applications]
        if not apps:
            return []
        return db.query(Interview).filter(Interview.result_id.in_(apps)).order_by(Interview.scheduled_at).all()
    else:
        # Recruiter
        job_ids = [job.id for job in user.jobs]
        if not job_ids:
            return []
            
        # Get all applications for jobs created by recruiter
        apps = db.query(Application).filter(Application.job_id.in_(job_ids)).all()
        app_ids = [a.id for a in apps]
        
        # Get all results for jobs created by recruiter
        results = db.query(Result).filter(Result.job_id.in_(job_ids)).all()
        result_ids = [r.id for r in results]
        
        all_ids = app_ids + result_ids
        if not all_ids:
            return []
            
        interviews = db.query(Interview).filter(Interview.result_id.in_(all_ids)).order_by(Interview.scheduled_at).all()
        return interviews

@router.patch("/{interview_id}", response_model=InterviewOut)
def update_interview(interview_id: str, data: InterviewUpdate, db: Session = Depends(get_db), user: User = Depends(require_recruiter)):
    interview = db.query(Interview).filter(Interview.id == interview_id).first()
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")
        
    update_data = data.model_dump(exclude_unset=True)
    for key, val in update_data.items():
        setattr(interview, key, val)
        
    db.commit()
    db.refresh(interview)
    return interview
