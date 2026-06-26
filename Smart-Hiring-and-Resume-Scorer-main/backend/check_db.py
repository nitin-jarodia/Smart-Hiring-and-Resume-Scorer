from app.database import SessionLocal
from app.models.domain import User, Job, Resume, Result

db = SessionLocal()
users = db.query(User).all()
print(f"Users: {len(users)}")
for u in users:
    print(f" - {u.email} ({u.role})")

jobs = db.query(Job).all()
print(f"Jobs: {len(jobs)}")
for j in jobs:
    resumes = db.query(Resume).filter(Resume.job_id == j.id).all()
    results = db.query(Result).filter(Result.job_id == j.id).all()
    print(f" - {j.title} (ID: {j.id}, Resumes: {len(resumes)}, Results: {len(results)})")

db.close()
