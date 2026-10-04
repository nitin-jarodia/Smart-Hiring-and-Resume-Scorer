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
Base.metadata.create_all(bind=engine)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    logger.info("ScreenerAI API starting up...")
    from .database import SessionLocal
    from .auth.security import get_password_hash

    if settings.is_dev_secret:
        logger.warning(
            "SECRET_KEY is still the development default. "
            "Set SECRET_KEY to a random secret before deploying."
        )

    # Seed an admin only when one is explicitly configured, or while running on the
    # development secret. A deployment with a real SECRET_KEY never gets a default login.
    seed_password = settings.SEED_ADMIN_PASSWORD
    if not seed_password and settings.is_dev_secret:
        seed_password = "admin123"

    db = SessionLocal()
    try:
        if not db.query(AppSettings).filter(AppSettings.id == 1).first():
            db.add(AppSettings(id=1, retention_days=90, fairness_guardrails=True))
            db.commit()

        if seed_password:
            admin = db.query(User).filter(User.email == settings.SEED_ADMIN_EMAIL).first()
            if not admin:
                db.add(User(
                    email=settings.SEED_ADMIN_EMAIL,
                    hashed_password=get_password_hash(seed_password),
                    full_name="Admin User",
                    role="admin",
                ))
                db.commit()
                logger.info(f"Created admin account: {settings.SEED_ADMIN_EMAIL}")
        else:
            logger.info("No SEED_ADMIN_PASSWORD set; skipping default admin creation.")
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
    allow_origins=settings.cors_origins,
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

