import os
import sys

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import app.ai.embeddings as embeddings
import app.models.domain  # noqa: F401
from app.ai.llm import answer_from_chunks
from app.ai.rag import build_chunks, index_text, retrieve
from app.database import Base
from app.models.domain import ResumeChunk


@pytest.fixture(autouse=True)
def hash_embeddings():
    embeddings._sentence_model = "fallback"
    yield


def test_build_chunks_labels_sections_and_splits_long_text():
    words = " ".join(f"word{i}" for i in range(200))
    text = f"EXPERIENCE\n{words}\n\nEDUCATION\nB.S. Computer Science"
    chunks = build_chunks(text)
    sections = {chunk["section"] for chunk in chunks}
    assert "experience" in sections
    assert "education" in sections
    assert len([chunk for chunk in chunks if chunk["section"] == "experience"]) >= 2


def test_build_chunks_uses_body_when_no_sections():
    chunks = build_chunks("Worked on python services for a retail checkout team and shipped weekly releases to production customers.")
    assert chunks
    assert all(chunk["section"] == "body" for chunk in chunks)


def test_stored_chunks_mask_email():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    db = sessionmaker(bind=engine)()
    text = "EXPERIENCE\nContact jane.doe@example.com about the billing migration and the on-call rotation."
    index_text(db, text, resume_id="resume-pii")
    rows = db.query(ResumeChunk).all()
    assert rows
    blob = " ".join(row.text for row in rows)
    assert "jane.doe@example.com" not in blob
    assert "[EMAIL]" in blob
    db.close()


def test_retrieve_returns_the_matching_passage():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    db = sessionmaker(bind=engine)()
    text = (
        "EXPERIENCE\n"
        "Led the quantum lattice migration for orbital billing using zylophone orchestration across twelve regions.\n\n"
        "EDUCATION\n"
        "Studied watercolor painting and ceramic glazing in a coastal studio for four years."
    )
    index_text(db, text, resume_id="resume-1")
    hits = retrieve(db, "quantum lattice migration zylophone", resume_id="resume-1", top_k=1)
    assert hits
    assert "zylophone" in hits[0]["text"].lower() or "quantum" in hits[0]["text"].lower()
    db.close()


def test_answer_without_model_returns_excerpts(monkeypatch):
    monkeypatch.setattr("app.ai.llm.has_openai", lambda: False)
    out = answer_from_chunks(
        "What did they lead?",
        [{"id": "c1", "section": "experience", "text": "Led a billing migration.", "similarity": 0.8}],
    )
    assert out["used_llm"] is False
    assert "billing migration" in out["answer"]
    assert out["citations"][0]["chunk_id"] == "c1"
    assert "No model key is configured." in out["answer"]
