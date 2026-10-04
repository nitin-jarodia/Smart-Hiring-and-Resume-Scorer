import numpy as np
import logging
from sqlalchemy.orm import Session
from ..models.domain import CandidateProfile, CandidateEmbedding
from .embeddings import embed_text, cosine_similarity

logger = logging.getLogger(__name__)

def update_candidate_embedding(candidate_id: str, text: str):
    """Generate and store a vector embedding using a fresh database session."""
    if not text or not text.strip():
        return

    from ..database import SessionLocal
    db = SessionLocal()
    try:
        emb_array = embed_text(text)
        emb_list = emb_array.tolist()

        record = db.query(CandidateEmbedding).filter(CandidateEmbedding.candidate_id == candidate_id).first()
        if record:
            record.embedding = emb_list
        else:
            record = CandidateEmbedding(candidate_id=candidate_id, embedding=emb_list)
            db.add(record)

        db.commit()
        logger.info(f"Updated vector embedding for candidate {candidate_id}")
    except Exception as e:
        logger.error(f"Failed to update candidate embedding: {e}")
        db.rollback()
    finally:
        db.close()

def search_candidates(db: Session, query: str, top_k: int = 10):
    """Perform a pure NumPy dot-product semantic search safely without FAISS."""
    try:
        if not query or not query.strip():
            return []

        query_emb = embed_text(query)
        
        # Load all embeddings
        # In a massive DB we'd use pgvector or FAISS, but for local/SQLite, NumPy in memory is incredibly fast for <1M vectors
        records = db.query(CandidateEmbedding).all()
        if not records:
            return []

        results = []
        for r in records:
            if not r.embedding: continue
            cand_emb = np.array(r.embedding, dtype=np.float32)
            sim = cosine_similarity(query_emb, cand_emb)
            results.append({
                "candidate_id": r.candidate_id,
                "similarity": sim
            })

        # Sort by highest similarity
        results.sort(key=lambda x: x["similarity"], reverse=True)
        top_results = results[:top_k]

        # Fetch candidate profiles for top results
        final_out = []
        for res in top_results:
            cand = db.query(CandidateProfile).filter(CandidateProfile.id == res["candidate_id"]).first()
            if cand:
                final_out.append({
                    "id": cand.id,
                    "filename": cand.filename,
                    "extracted_skills": cand.extracted_skills,
                    "overall_score": cand.overall_score,
                    "similarity": round(res["similarity"], 3)
                })

        return final_out
    except Exception as e:
        logger.error(f"Semantic search failed gracefully: {e}")
        return []
