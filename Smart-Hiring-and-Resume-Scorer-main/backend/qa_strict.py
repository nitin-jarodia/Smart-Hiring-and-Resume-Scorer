"""
Strict QA pass (backend-first).

This script runs end-to-end API flows using FastAPI TestClient without requiring
running servers. It validates:
- Auth + role-based guards
- Candidate profile upload + recommendations + apply + applications
- Recruiter job create + results + status update
- Interview scheduling + candidate visibility
"""

from __future__ import annotations

import io
import time
from typing import Any, Dict, Optional

from fastapi.testclient import TestClient


def assert_true(cond: bool, msg: str) -> None:
    if not cond:
        raise AssertionError(msg)


def assert_keys(d: Dict[str, Any], keys: list[str], ctx: str) -> None:
    missing = [k for k in keys if k not in d]
    assert_true(not missing, f"{ctx}: missing keys: {missing}")


def main() -> None:
    # Import app late to ensure settings are loaded normally
    from app.main import app  # noqa: WPS433

    client = TestClient(app)

    uniq = int(time.time() * 1000)
    recruiter_email = f"recruiter_{uniq}@qa.dev"
    candidate_email = f"candidate_{uniq}@qa.dev"
    recruiter_pw = "recruiter123"
    candidate_pw = "candidate123"

    # ---- Auth: signup + login + me ----
    r_signup = client.post(
        "/auth/signup",
        json={
            "email": recruiter_email,
            "password": recruiter_pw,
            "full_name": "QA Recruiter",
            "role": "recruiter",
        },
    )
    assert_true(r_signup.status_code == 200, f"Recruiter signup failed: {r_signup.text}")
    recruiter_tok = r_signup.json()
    assert_keys(recruiter_tok, ["access_token", "token_type", "user"], "recruiter token")
    assert_true(recruiter_tok["user"]["role"] == "recruiter", "Recruiter role mismatch")

    c_signup = client.post(
        "/auth/signup",
        json={
            "email": candidate_email,
            "password": candidate_pw,
            "full_name": "QA Candidate",
            "role": "candidate",
        },
    )
    assert_true(c_signup.status_code == 200, f"Candidate signup failed: {c_signup.text}")
    candidate_tok = c_signup.json()
    assert_keys(candidate_tok, ["access_token", "token_type", "user"], "candidate token")
    assert_true(candidate_tok["user"]["role"] == "candidate", "Candidate role mismatch")

    r_login = client.post("/auth/login", json={"email": recruiter_email, "password": recruiter_pw})
    assert_true(r_login.status_code == 200, f"Recruiter login failed: {r_login.text}")
    c_login = client.post("/auth/login", json={"email": candidate_email, "password": candidate_pw})
    assert_true(c_login.status_code == 200, f"Candidate login failed: {c_login.text}")

    me_r = client.get("/auth/me", headers={"Authorization": f"Bearer {recruiter_tok['access_token']}"})
    assert_true(me_r.status_code == 200, f"/auth/me recruiter failed: {me_r.text}")
    me_c = client.get("/auth/me", headers={"Authorization": f"Bearer {candidate_tok['access_token']}"})
    assert_true(me_c.status_code == 200, f"/auth/me candidate failed: {me_c.text}")

    # ---- Guards ----
    # Candidate blocked from recruiter-only GET /jobs
    jobs_as_candidate = client.get("/jobs", headers={"Authorization": f"Bearer {candidate_tok['access_token']}"})
    assert_true(jobs_as_candidate.status_code == 403, f"Candidate should be blocked from /jobs: {jobs_as_candidate.text}")

    # Recruiter blocked from candidate-only GET /candidate/profile
    prof_as_recruiter = client.get("/candidate/profile", headers={"Authorization": f"Bearer {recruiter_tok['access_token']}"})
    assert_true(
        prof_as_recruiter.status_code == 403,
        f"Recruiter should be blocked from /candidate/profile: {prof_as_recruiter.text}",
    )

    # ---- Recruiter creates job ----
    job_create = client.post(
        "/jobs",
        headers={"Authorization": f"Bearer {recruiter_tok['access_token']}"},
        json={
            "title": "QA Backend Engineer",
            "company": "QA Inc",
            "jd_text": "Looking for backend engineer with Python, FastAPI, SQL, Docker. 3+ years experience.",
            "required_skills": ["python", "fastapi", "sql", "docker"],
            "nice_to_have_skills": [],
            "min_years_exp": 3,
        },
    )
    assert_true(job_create.status_code == 200, f"Job create failed: {job_create.text}")
    job = job_create.json()
    assert_keys(job, ["id", "title", "jd_text", "required_skills", "created_at"], "job out")
    job_id = job["id"]

    # Recruiter sees own jobs
    job_list = client.get("/jobs", headers={"Authorization": f"Bearer {recruiter_tok['access_token']}"})
    assert_true(job_list.status_code == 200, f"Job list failed: {job_list.text}")
    assert_true(any(j.get("id") == job_id for j in job_list.json()), "Created job not in recruiter /jobs list")

    # Candidate can browse public jobs
    public_jobs = client.get("/jobs/public")
    assert_true(public_jobs.status_code == 200, f"Public jobs failed: {public_jobs.text}")
    assert_true(any(j.get("id") == job_id for j in public_jobs.json()), "Created job not in /jobs/public")

    # ---- Candidate uploads resume ----
    resume_text = (
        f"QA Candidate\nEmail: {candidate_email}\n\n"
        "Skills: Python, FastAPI, SQL, Docker\n"
        "Experience: 4 years building APIs in Python and FastAPI.\n"
    )
    file_bytes = io.BytesIO(resume_text.encode("utf-8"))
    upload = client.post(
        "/candidate/profile",
        headers={"Authorization": f"Bearer {candidate_tok['access_token']}"},
        files={"file": ("resume.txt", file_bytes, "text/plain")},
    )
    assert_true(upload.status_code == 200, f"Candidate resume upload failed: {upload.text}")

    profile = client.get("/candidate/profile", headers={"Authorization": f"Bearer {candidate_tok['access_token']}"})
    assert_true(profile.status_code == 200, f"Candidate get profile failed: {profile.text}")
    prof = profile.json()
    assert_true(prof.get("has_profile") is True, "Candidate has_profile should be true")
    assert_true(isinstance(prof.get("overall_score"), (int, float)), "Candidate overall_score missing/invalid")
    assert_true(isinstance(prof.get("extracted_skills"), list), "Candidate extracted_skills missing/invalid")
    assert_true("seniority" in prof, "Candidate seniority missing")

    # Candidate tips / suggestions / recs should be shaped
    tips = client.get("/candidate/resume-tips", headers={"Authorization": f"Bearer {candidate_tok['access_token']}"})
    assert_true(tips.status_code == 200, f"Resume tips failed: {tips.text}")
    assert_true(isinstance(tips.json(), list), "Resume tips response not list")

    sugg = client.get("/candidate/skills-suggestions", headers={"Authorization": f"Bearer {candidate_tok['access_token']}"})
    assert_true(sugg.status_code == 200, f"Skill suggestions failed: {sugg.text}")
    assert_true(isinstance(sugg.json(), list), "Skill suggestions response not list")

    recs = client.get("/candidate/recommendations", headers={"Authorization": f"Bearer {candidate_tok['access_token']}"})
    assert_true(recs.status_code == 200, f"Recommendations failed: {recs.text}")
    assert_true(isinstance(recs.json(), list), "Recommendations response not list")

    # ---- Candidate applies ----
    apply = client.post(
        f"/candidate/apply/{job_id}",
        headers={"Authorization": f"Bearer {candidate_tok['access_token']}"},
    )
    assert_true(apply.status_code == 200, f"Apply failed: {apply.text}")
    apply_data = apply.json()
    assert_keys(apply_data, ["application_id", "score", "match_percent", "matched_skills", "missing_skills"], "apply response")

    apps = client.get("/candidate/applications", headers={"Authorization": f"Bearer {candidate_tok['access_token']}"})
    assert_true(apps.status_code == 200, f"Candidate applications failed: {apps.text}")
    apps_list = apps.json()
    assert_true(len(apps_list) == 1, "Expected 1 application in candidate applications list")
    assert_true(apps_list[0]["status"] == "pending", "Expected pending status after apply")

    # ---- Recruiter sees ranked results and can update status ----
    results = client.get(f"/jobs/{job_id}/results", headers={"Authorization": f"Bearer {recruiter_tok['access_token']}"})
    assert_true(results.status_code == 200, f"Recruiter results failed: {results.text}")
    results_list = results.json()
    assert_true(len(results_list) >= 1, "Expected at least 1 result in recruiter results list")

    picked: Optional[Dict[str, Any]] = None
    for r in results_list:
        if r.get("candidate_email") == candidate_email:
            picked = r
            break
    picked = picked or results_list[0]
    assert_true("id" in picked, "Result item missing id")

    upd = client.patch(
        f"/results/{picked['id']}",
        headers={"Authorization": f"Bearer {recruiter_tok['access_token']}"},
        json={"status": "shortlisted"},
    )
    assert_true(upd.status_code == 200, f"Recruiter status update failed: {upd.text}")

    apps2 = client.get("/candidate/applications", headers={"Authorization": f"Bearer {candidate_tok['access_token']}"})
    assert_true(apps2.status_code == 200, f"Candidate applications after update failed: {apps2.text}")
    assert_true(apps2.json()[0]["status"] == "shortlisted", "Recruiter-updated status did not reflect on candidate applications")

    # ---- Recruiter schedules interview and candidate sees meeting link ----
    scheduled_at = "2030-01-01T10:00:00Z"
    inter = client.post(
        "/interviews",
        headers={"Authorization": f"Bearer {recruiter_tok['access_token']}"},
        json={
            "result_id": picked["id"],
            "scheduled_at": scheduled_at,
            "duration_minutes": 30,
            "meeting_link": "https://example.com/meet/demo",
            "notes": "Demo interview",
        },
    )
    assert_true(inter.status_code == 200, f"Schedule interview failed: {inter.text}")

    cand_interviews = client.get("/interviews/my-interviews", headers={"Authorization": f"Bearer {candidate_tok['access_token']}"})
    assert_true(cand_interviews.status_code == 200, f"Candidate my-interviews failed: {cand_interviews.text}")
    ci = cand_interviews.json()
    assert_true(isinstance(ci, list) and len(ci) >= 1, "Candidate interviews list empty")
    assert_true(ci[0]["meeting_link"] == "https://example.com/meet/demo", "Candidate meeting_link mismatch")

    print("STRICT_QA_PASS")


if __name__ == "__main__":
    main()

