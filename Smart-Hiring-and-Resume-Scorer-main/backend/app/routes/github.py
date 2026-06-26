from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel

from ..database import get_db
from ..models.domain import User, CandidateGitHub, CandidateProfile
from ..auth.security import get_current_user, require_candidate
from ..ai.github_analyzer import analyze_and_store_github

router = APIRouter(tags=["github"])

class GitHubSubmitReq(BaseModel):
    github_url: str

@router.post("/candidate/github")
async def submit_github_profile(
    req: GitHubSubmitReq,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_candidate),
):
    """Link GitHub to Candidate profile and start background analysis."""
    profile = db.query(CandidateProfile).filter(CandidateProfile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=400, detail="Please upload a resume first")
        
    # Start analysis task
    background_tasks.add_task(analyze_and_store_github, db, profile.id, req.github_url)
    
    return {"message": "GitHub profile linking started in the background"}

@router.get("/candidate/github/{candidate_id}")
def get_candidate_github(
    candidate_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve GitHub stats for a specific candidate."""
    gh = db.query(CandidateGitHub).filter(CandidateGitHub.candidate_id == candidate_id).first()
    if not gh:
        return {"has_github": False}
        
    return {
        "has_github": True,
        "github_url": gh.github_url,
        "username": gh.username,
        "metrics": gh.metrics,
        "top_languages": gh.top_languages,
        "updated_at": gh.updated_at
    }
