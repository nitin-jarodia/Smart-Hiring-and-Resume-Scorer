import os
import uuid
import aiofiles
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..models.domain import Job, Resume
from ..models.schemas import ResumeOut
from ..auth.security import require_recruiter
from ..ai.parser import extract_text, extract_contact_info, detect_sections
from ..config import settings

router = APIRouter(tags=["resumes"])

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".doc", ".txt"}
MAX_SIZE = settings.MAX_FILE_SIZE_MB * 1024 * 1024

@router.post("/jobs/{job_id}/resumes", response_model=List[ResumeOut])
async def upload_resumes(
    job_id: str,
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
    current_user=Depends(require_recruiter),
):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    results = []
    for file in files:
        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(status_code=400, detail=f"File type {ext} not allowed")
        
        content = await file.read()
        if len(content) > MAX_SIZE:
            raise HTTPException(status_code=400, detail="File too large")
        
        file_id = str(uuid.uuid4())
        save_path = os.path.join(settings.UPLOAD_DIR, f"{file_id}{ext}")
        
        async with aiofiles.open(save_path, "wb") as f:
            await f.write(content)
        
        # Extract text
        extracted_text = extract_text(save_path)
        contact = extract_contact_info(extracted_text)
        sections = detect_sections(extracted_text)
        
        resume = Resume(
            job_id=job_id,
            filename=file.filename,
            file_path=save_path,
            extracted_text=extracted_text,
            candidate_name=contact.get("name", ""),
            email=contact.get("email", ""),
            phone=contact.get("phone", ""),
            sections=sections,
        )
        db.add(resume)
        db.commit()
        db.refresh(resume)
        results.append(ResumeOut.model_validate(resume))
    
    return results

@router.get("/jobs/{job_id}/resumes", response_model=List[ResumeOut])
def list_resumes(job_id: str, db: Session = Depends(get_db), current_user=Depends(require_recruiter)):
    resumes = db.query(Resume).filter(Resume.job_id == job_id).all()
    return [ResumeOut.model_validate(r) for r in resumes]

@router.get("/resumes/{resume_id}", response_model=ResumeOut)
def get_resume(resume_id: str, db: Session = Depends(get_db), current_user=Depends(require_recruiter)):
    resume = db.query(Resume).filter(Resume.id == resume_id).first()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    return ResumeOut.model_validate(resume)

@router.delete("/resumes/{resume_id}")
def delete_resume(resume_id: str, db: Session = Depends(get_db), current_user=Depends(require_recruiter)):
    resume = db.query(Resume).filter(Resume.id == resume_id).first()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    if os.path.exists(resume.file_path):
        os.remove(resume.file_path)
    db.delete(resume)
    db.commit()
    return {"message": "Resume deleted"}
