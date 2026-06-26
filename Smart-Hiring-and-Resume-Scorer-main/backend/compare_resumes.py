"""
Resume Comparison Test: Run fraud, low-quality, and perfect resumes through ScreenerAI.
Uses the LIVE backend at http://localhost:8000.
"""
import requests
import json
import os

BASE = "http://localhost:8000"
RESUME_DIR = r"c:\Users\om\Documents\coding\My Notebook\Side projects\resume-screener"

# --- 1. Authenticate as recruiter ---
reg = requests.post(f"{BASE}/auth/signup", json={
    "email": "compare_test_recruiter@test.com",
    "password": "Test1234!",
    "full_name": "Test Recruiter",
    "role": "recruiter"
})
if reg.status_code not in (200, 201, 400):  # 400 = already exists
    print(f"Signup failed: {reg.status_code} {reg.text}")
    exit(1)

login = requests.post(f"{BASE}/auth/login", json={
    "email": "compare_test_recruiter@test.com",
    "password": "Test1234!"
})
if login.status_code != 200:
    print(f"Login failed: {login.status_code} {login.text}")
    exit(1)

token = login.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}
print("[OK] Recruiter authenticated")

# --- 2. Create a Software Engineer job ---
jd = requests.post(f"{BASE}/jobs", headers=headers, json={
    "title": "Senior Software Engineer",
    "company": "TechCorp",
    "jd_text": """We need a Senior Software Engineer with 5+ years of experience.
Required: Python, FastAPI, PostgreSQL, Docker, AWS, REST APIs, CI/CD, Git.
Nice to have: Kubernetes, React, TypeScript.
Must have proven track record with measurable impact on systems and teams.
Strong communication and leadership skills required.""",
    "required_skills": ["Python", "FastAPI", "PostgreSQL", "Docker", "AWS", "REST APIs", "CI/CD", "Git"],
    "min_years_exp": 5
})
if jd.status_code not in (200, 201):
    print(f"Job creation failed: {jd.status_code} {jd.text}")
    exit(1)
job_id = jd.json()["id"]
print(f"[OK] Job created: {job_id}")

# --- 3. Upload each resume and screen ---
resumes = {
    "fraud": "fraud_resume_test.pdf",
    "low_quality": "low_quality_resume_test.pdf",
    "perfect": "perfect_resume_test.pdf",
}

for label, filename in resumes.items():
    path = os.path.join(RESUME_DIR, filename)
    if not os.path.exists(path):
        print(f"[ERROR] File not found: {path}")
        continue

    with open(path, "rb") as f:
        upload = requests.post(
            f"{BASE}/jobs/{job_id}/resumes",
            headers=headers,
            files=[("files", (filename, f, "application/pdf"))]
        )
    if upload.status_code not in (200, 201):
        print(f"[ERROR] Upload failed for {label}: {upload.status_code} {upload.text}")
        continue

    resume_id = upload.json()[0]["id"]
    print(f"[OK] Uploaded {label}: resume_id={resume_id}")

# --- 4. Screen all resumes ---
screen = requests.post(f"{BASE}/jobs/{job_id}/screen", headers=headers)
print(f"[OK] Screening initiated: {screen.status_code}")

# --- 5. Fetch results ---
results_resp = requests.get(f"{BASE}/jobs/{job_id}/results", headers=headers)
if results_resp.status_code != 200:
    print(f"[ERROR] Results fetch failed: {results_resp.status_code} {results_resp.text}")
    exit(1)

results = results_resp.json()
print(f"\n{'='*70}")
print(f"{'SCREENERIAI RESUME COMPARISON REPORT':^70}")
print(f"{'='*70}\n")

for r in results:
    print(f"\n--- CANDIDATE: {r.get('candidate_name','[no name]')} | filename: {r.get('filename','N/A')} ---")
    print(f"  SCORE         : {r.get('score', 0):.1f}/100")
    print(f"  SENIORITY     : {r.get('seniority','N/A')}")
    print(f"  MATCHED SKILLS: {r.get('matched_skills', [])}")
    fraud = r.get("fraud_flags", [])
    print(f"  FRAUD FLAGS   : {len(fraud)} flag(s)")
    for f in fraud:
        print(f"    [!] [{f.get('severity','?')}] {f.get('reason','')}")

    tags = r.get("strength_tags", [])
    if tags:
        print(f"  STRENGTH TAGS : {', '.join(tags)}")

    red_flags = r.get("red_flags", [])
    if red_flags:
        print(f"  RED FLAGS     :")
        for rf in red_flags[:3]:
            print(f"    [RED] {rf}")

    evidence = r.get("evidence", [])
    print(f"  EVIDENCE SNIPPETS: {len(evidence)} found")

    recs = r.get("recommendations", [])
    print(f"  RECOMMENDATIONS ({len(recs)}):")
    for rec in recs[:3]:
        print(f"    - {rec[:100]}")

    proj = r.get("project_evaluations", [])
    print(f"  PROJECTS EVALUATED: {len(proj)}")
    for p in proj[:2]:
        print(f"    [PROJ] {p.get('name','?')} -> Grade: {p.get('grade','?')}")

    print(f"  EXPLANATION   : {r.get('explanation','')[:200]}")
    print()

# --- 6. Machine-readable JSON dump ---
print("\n\n--- RAW JSON (for analysis) ---")
print(json.dumps(results, indent=2, default=str)[:8000])
