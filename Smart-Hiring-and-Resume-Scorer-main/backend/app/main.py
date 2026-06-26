from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
logger = logging.getLogger(__name__)
import os

from .database import engine, Base
from .models.domain import User, Job, Resume, Result, AppSettings, CandidateProfile, Application, Interview
from .routes import auth, jobs, resumes, screening, analytics, candidate, interviews, search, github
from .config import settings

# Create all tables
if settings.AUTO_CREATE_TABLES:
    Base.metadata.create_all(bind=engine)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    logger.info("ScreenerAI API starting up...")
    from .database import SessionLocal
    from .auth.security import get_password_hash
    db = SessionLocal()
    try:
        admin = db.query(User).filter(User.email == "admin@screener.dev").first()
        if not admin:
            db.add(User(
                email="admin@screener.dev",
                hashed_password=get_password_hash("admin123"),
                full_name="Admin User",
                role="admin",
            ))
            db.add(AppSettings(id=1, retention_days=90, fairness_guardrails=True))
            db.commit()
            logger.info("Created default admin: admin@screener.dev / admin123")
    except Exception as e:
        logger.error(f"Startup error: {e}")
        db.rollback()
    finally:
        db.close()
    yield

app = FastAPI(
    title="Resume Screener API",
    description="Intelligent Resume Screening Tool — AI-Driven Analysis",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(jobs.router)
app.include_router(resumes.router)
app.include_router(screening.router)
app.include_router(analytics.router)
app.include_router(candidate.router)
app.include_router(interviews.router)
app.include_router(search.router)
app.include_router(github.router)

@app.get("/health")
def health():
    return {"status": "ok", "version": "1.0.0"}

@app.get("/")
def root():
    return {
        "message": "ScreenerAI Resume Screener API",
        "docs": "/docs",
        "fairness_guardrails": True,
        "scoring": "skills + experience only — no personal attributes used"
    }

