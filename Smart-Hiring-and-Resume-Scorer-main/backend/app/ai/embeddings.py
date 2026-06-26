import numpy as np
import hashlib
import re
from typing import List, Tuple
import logging
logger = logging.getLogger(__name__)

_sentence_model = None
_EMBED_DIM = 384

def get_sentence_model():
    global _sentence_model
    if _sentence_model is None:
        try:
            from sentence_transformers import SentenceTransformer
            _sentence_model = SentenceTransformer('all-MiniLM-L6-v2')
            logger.info("Loaded sentence-transformer model: all-MiniLM-L6-v2")
        except Exception as e:
            logger.warning(f"sentence-transformers not available ({e}). Using hash-based fallback.")
            _sentence_model = "fallback"
    return _sentence_model

def _hash_embed(text: str, dim: int = _EMBED_DIM) -> np.ndarray:
    """
    Stable hash-based embedding. Same text → same vector. Different texts → different vectors.
    Uses token-level hashing into a fixed-size float vector.
    """
    tokens = re.findall(r'\b\w+\b', text.lower())
    vec = np.zeros(dim, dtype=np.float32)
    for token in tokens:
        h = int(hashlib.md5(token.encode()).hexdigest(), 16)
        idx = h % dim
        # Use a second hash for value to spread signal
        val = (int(hashlib.sha1(token.encode()).hexdigest(), 16) % 1000) / 1000.0 - 0.5
        vec[idx] += val
    norm = np.linalg.norm(vec)
    return vec / norm if norm > 0 else vec

def embed_text(text: str) -> np.ndarray:
    """Embed text using sentence-transformers or hash fallback."""
    if not text or not text.strip():
        return np.zeros(_EMBED_DIM, dtype=np.float32)
    
    model = get_sentence_model()
    if model == "fallback":
        return _hash_embed(text, _EMBED_DIM)
    
    try:
        emb = model.encode(text, convert_to_numpy=True)
        return emb.astype(np.float32)
    except Exception as e:
        logger.error(f"Embedding failed: {e}")
        return _hash_embed(text, _EMBED_DIM)

def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Compute cosine similarity. Both vectors must have same dimension."""
    if a is None or b is None:
        return 0.0
    # Ensure same dimension by padding/truncating
    if len(a) != len(b):
        min_len = min(len(a), len(b))
        a, b = a[:min_len], b[:min_len]
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))

def chunk_text(text: str, chunk_size: int = 400, overlap: int = 50) -> List[str]:
    """Split text into overlapping word chunks."""
    words = text.split()
    if not words:
        return []
    chunks = []
    i = 0
    while i < len(words):
        chunk = ' '.join(words[i:i + chunk_size])
        chunks.append(chunk)
        i += chunk_size - overlap
    return chunks

def get_top_evidence_chunks(resume_text: str, jd_text: str, top_k: int = 3) -> List[Tuple[str, float]]:
    """Find most relevant resume passages vs JD."""
    chunks = chunk_text(resume_text)
    if not chunks:
        return []
    jd_emb = embed_text(jd_text)
    scored = [(chunk, cosine_similarity(jd_emb, embed_text(chunk))) for chunk in chunks]
    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[:top_k]
