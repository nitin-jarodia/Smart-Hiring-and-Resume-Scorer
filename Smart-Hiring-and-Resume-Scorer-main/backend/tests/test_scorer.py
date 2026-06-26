import pytest
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

JD_TEXT = """Senior Backend Engineer. Required: Python, PostgreSQL, AWS, Docker, Kubernetes, 
microservices, REST APIs. 5+ years experience."""

STRONG_RESUME = """Alice Chen - Senior Engineer with 7 years experience.
Skills: Python, FastAPI, PostgreSQL, Redis, AWS, Docker, Kubernetes, Terraform, CI/CD.
Led microservices migration. Built REST APIs. B.S. Computer Science."""

WEAK_RESUME = """Emma Patel - Recent graduate. Internship 3 months.
Skills: Python, Flask, SQLite. Basic Docker."""

def test_strong_resume_scores_high():
    from app.ai.scorer import score_resume
    result = score_resume(JD_TEXT, STRONG_RESUME)
    assert result["score"] >= 60
    assert len(result["matched_skills"]) >= 3

def test_weak_resume_scores_lower():
    from app.ai.scorer import score_resume
    strong = score_resume(JD_TEXT, STRONG_RESUME)
    weak = score_resume(JD_TEXT, WEAK_RESUME)
    assert strong["score"] > weak["score"]

def test_result_has_required_fields():
    from app.ai.scorer import score_resume
    result = score_resume(JD_TEXT, STRONG_RESUME)
    required_keys = ["score", "confidence", "seniority", "breakdown", "matched_skills", "missing_skills"]
    for key in required_keys:
        assert key in result

def test_score_range():
    from app.ai.scorer import score_resume
    result = score_resume(JD_TEXT, STRONG_RESUME)
    assert 0 <= result["score"] <= 100
