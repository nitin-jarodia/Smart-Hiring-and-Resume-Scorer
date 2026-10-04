"""Chunk resumes at upload time and retrieve passages for grounded answers."""
import logging
from typing import Dict, List, Optional

import numpy as np
from sqlalchemy.orm import Session

from ..models.domain import ResumeChunk
from .embeddings import cosine_similarity, embed_text
from .llm import answer_from_chunks
from .parser import detect_sections, mask_pii

logger = logging.getLogger(__name__)

CHUNK_WORDS = 120
CHUNK_OVERLAP = 30
_MIN_TAIL_WORDS = 20


def _windows(words: List[str]) -> List[str]:
    if not words:
        return []
    if len(words) <= CHUNK_WORDS:
        return [" ".join(words)]
    step = CHUNK_WORDS - CHUNK_OVERLAP
    windows: List[str] = []
    i = 0
    while i < len(words):
        window = words[i:i + CHUNK_WORDS]
        if len(window) < _MIN_TAIL_WORDS and windows:
            break
        windows.append(" ".join(window))
        if i + CHUNK_WORDS >= len(words):
            break
        i += step
    return windows


def build_chunks(text: str) -> List[Dict[str, str]]:
    """Split masked resume text into section-labeled word windows."""
    masked = mask_pii(text or "")
    if not masked.strip():
        return []

    sections = detect_sections(masked)
    named = {key: body for key, body in sections.items() if key != "header" and body and body.strip()}
    blocks = list(named.items()) if named else [("body", masked)]

    chunks: List[Dict[str, str]] = []
    index = 0
    for section, body in blocks:
        for window in _windows(body.split()):
            cleaned = window.strip()
            if not cleaned:
                continue
            chunks.append({
                "section": section,
                "chunk_index": str(index),
                "text": cleaned,
            })
            index += 1
    return chunks


def _owner_query(db: Session, resume_id: Optional[str], candidate_id: Optional[str]):
    query = db.query(ResumeChunk)
    if resume_id:
        return query.filter(ResumeChunk.resume_id == resume_id)
    if candidate_id:
        return query.filter(ResumeChunk.candidate_id == candidate_id)
    raise ValueError("resume_id or candidate_id is required")


def owner_has_chunks(db: Session, resume_id: Optional[str] = None, candidate_id: Optional[str] = None) -> bool:
    return _owner_query(db, resume_id, candidate_id).first() is not None


def index_text(
    db: Session,
    text: str,
    resume_id: Optional[str] = None,
    candidate_id: Optional[str] = None,
) -> int:
    """Replace this owner's chunks with a fresh index. Returns the chunk count."""
    if not resume_id and not candidate_id:
        raise ValueError("resume_id or candidate_id is required")

    _owner_query(db, resume_id, candidate_id).delete(synchronize_session=False)
    chunks = build_chunks(text)
    for chunk in chunks:
        emb = embed_text(chunk["text"])
        db.add(ResumeChunk(
            resume_id=resume_id,
            candidate_id=candidate_id,
            section=chunk["section"],
            chunk_index=int(chunk["chunk_index"]),
            text=chunk["text"],
            embedding=emb.tolist() if hasattr(emb, "tolist") else list(emb),
        ))
    db.commit()
    logger.info(
        "Indexed %s chunks for resume=%s candidate=%s",
        len(chunks), resume_id, candidate_id,
    )
    return len(chunks)


def ensure_indexed(
    db: Session,
    text: str,
    resume_id: Optional[str] = None,
    candidate_id: Optional[str] = None,
) -> None:
    if owner_has_chunks(db, resume_id=resume_id, candidate_id=candidate_id):
        return
    if text and text.strip():
        index_text(db, text, resume_id=resume_id, candidate_id=candidate_id)


def retrieve(
    db: Session,
    query: str,
    resume_id: Optional[str] = None,
    candidate_id: Optional[str] = None,
    top_k: int = 5,
) -> List[Dict]:
    """Rank one owner's chunks against a query."""
    if not query or not str(query).strip():
        return []
    rows = _owner_query(db, resume_id, candidate_id).all()
    if not rows:
        return []

    query_emb = embed_text(query)
    scored = []
    for row in rows:
        if not row.embedding:
            continue
        emb = np.array(row.embedding, dtype=np.float32)
        sim = cosine_similarity(query_emb, emb)
        scored.append((float(sim), row))
    scored.sort(key=lambda item: item[0], reverse=True)

    hits = []
    for sim, row in scored[:top_k]:
        hits.append({
            "id": row.id,
            "section": row.section or "",
            "text": row.text or "",
            "similarity": sim,
            "chunk_index": row.chunk_index,
        })
    return hits


def grounded_explanation(
    db: Session,
    jd_text: str,
    resume_text: str,
    resume_id: Optional[str] = None,
    candidate_id: Optional[str] = None,
) -> Dict:
    """Retrieve passages for a job description and write a cited fit summary."""
    ensure_indexed(db, resume_text, resume_id=resume_id, candidate_id=candidate_id)
    hits = retrieve(
        db,
        jd_text or "",
        resume_id=resume_id,
        candidate_id=candidate_id,
        top_k=5,
    )
    question = (
        "In 3 to 4 sentences, assess how this resume fits the job. "
        "Use only the excerpts. Cite chunk ids in square brackets.\n\n"
        f"Job description:\n{(jd_text or '')[:1500]}"
    )
    return answer_from_chunks(question, hits)


def citation_evidence(citations: List[Dict]) -> List[Dict]:
    """Shape retrieved passages for the existing Result.evidence list."""
    evidence = []
    for citation in citations:
        evidence.append({
            "skill": "citation",
            "type": "citation",
            "excerpt": citation.get("excerpt") or "",
            "chunk_id": citation.get("chunk_id") or "",
            "section": citation.get("section") or "",
            "similarity": citation.get("similarity"),
        })
    return evidence
