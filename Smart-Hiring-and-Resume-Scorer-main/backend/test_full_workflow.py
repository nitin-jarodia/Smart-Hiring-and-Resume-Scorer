import os
import sys
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Ensure backend directory is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__))))

from app.main import app
from app.database import get_db, Base
from app.models.domain import User, Job

# Define test database
db_file = "./test_app.db"
if os.path.exists(db_file):
    os.remove(db_file)

SQLALCHEMY_DATABASE_URL = f"sqlite:///{db_file}"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

def test_workflow():
    db = TestingSessionLocal()
    
    # 1. Register Recruiter
    recruiter = User(
        id="mock_recruiter123",
        email="recruiter@example.com",
        hashed_password="hashed_pass",
        full_name="Mock Recruiter",
        role="recruiter"
    )
    db.add(recruiter)
    db.commit()

    # 1.5 Provide mock job
    job = Job(
        title="Software Engineer",
        company="Tech Corp",
        jd_text="Looking for a Python developer with FastAPI and React experience.",
        required_skills=["Python", "FastAPI", "React", "SQL"],
        created_by="mock_recruiter123"
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    
    print(f"Created Job: {job.id} - {job.title}")

    # 2. Register Candidate
    register_response = client.post(
        "/auth/signup",
        json={"email": "candidate_test1@example.com", "password": "password123", "full_name": "Test Candidate", "role": "candidate"}
    )
    assert register_response.status_code == 200, f"Register failed: {register_response.text}"
    print("Registered Candidate successfully.")

    # 3. Login Candidate
    login_response = client.post(
        "/auth/login",
        json={"email": "candidate_test1@example.com", "password": "password123"}
    )
    assert login_response.status_code == 200, f"Login failed: {login_response.text}"
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("Logged in Candidate successfully.")

    # 4. Upload Resume
    # Create a dummy PDF or TXT
    dummy_resume = b"Test Resume. I developed a Python API using FastAPI. I increased performance by 50%."
    files = {"file": ("resume.txt", dummy_resume, "text/plain")}
    upload_res = client.post("/candidate/profile", files=files, headers=headers)
    assert upload_res.status_code == 200, f"Resume upload failed: {upload_res.text}"
    print("Uploaded Resume successfully.")
    
    # 5. Get Profile to ensure it parsed
    profile_res = client.get("/candidate/profile", headers=headers)
    assert profile_res.status_code == 200
    print("Fetched Profile successfully.")

    # 6. Apply to Job
    apply_res = client.post(f"/candidate/apply/{job.id}", headers=headers)
    assert apply_res.status_code == 200, f"Apply to job failed: {apply_res.text}"
    
    apply_data = apply_res.json()
    print(f"Applied to Job Successfully! Result ID: {apply_data.get('id')}")
    print(f"Score: {apply_data.get('score')}")
    assert apply_data.get("score") is not None and apply_data.get("score") > 0, "Score is zero or missing!"

    # 7. Get Resume Tips (to check dynamic review)
    tips_res = client.get("/candidate/resume-tips", headers=headers)
    assert tips_res.status_code == 200
    tips = tips_res.json()
    print("--- Dynamic Resume Tips ---")
    for tip in tips:
        print(f"[{tip['category']}] {tip['tip']}")

    print("ALL TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    test_workflow()
