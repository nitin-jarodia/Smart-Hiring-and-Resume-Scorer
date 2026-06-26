from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional

from ..database import get_db
from ..auth.security import require_recruiter
from ..ai.vector_search import search_candidates

router = APIRouter(tags=["search"])

class SemanticSearchQuery(BaseModel):
    query: str
    top_k: int = 10

@router.post("/search/candidates/semantic")
def perform_semantic_search(
    request: SemanticSearchQuery,
    db: Session = Depends(get_db),
    current_user=Depends(require_recruiter),
):
    """
    Perform a natural language semantic search across all candidate resumes.
    Example query: 'Looking for a senior frontend dev who knows React and GraphQL'
    """
    try:
        results = search_candidates(db, request.query, request.top_k)
        return {"query": request.query, "results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
