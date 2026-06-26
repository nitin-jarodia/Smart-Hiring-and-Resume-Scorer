# ScreenerAI — Setup Guide

Run the project from scratch in 3 steps.

## Prerequisites

- **Python 3.10+** — [python.org/downloads](https://www.python.org/downloads/)
- **Node.js 18+** — [nodejs.org](https://nodejs.org/)
- **Git** — [git-scm.com](https://git-scm.com/)

---

## Step 1 — Backend

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate it
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy env file
cp .env.example .env

# Start the server
uvicorn app.main:app --reload --port 8000
```

The API runs at **http://localhost:8000**

### Seed sample data (optional)

In a new terminal (with venv activated):

```bash
cd backend
python seed_data.py
```

This creates demo accounts:

- **Admin:** `admin@screener.dev` / `admin123`
- **Recruiter:** `recruiter@screener.dev` / `recruiter123`

---

## Step 2 — Frontend

```bash
cd frontend

# Install packages
cd frontend

# Create env file
echo NEXT_PUBLIC_API_URL=http://localhost:8000 > .env.local

# Start dev server
npm run dev
```

The app runs at **http://localhost:3000**

---

## Step 3 — Open & Use

1. Go to **http://localhost:3000**
2. Sign up or log in with seeded credentials
3. Create a job → Upload resumes → Run AI screening

---

## Project Structure

```
resume-screener/
├── backend/
│   ├── app/
│   │   ├── main.py          # FastAPI entry point
│   │   ├── models.py        # Database models
│   │   ├── schemas.py       # API schemas
│   │   ├── routers/         # API routes
│   │   ├── services/        # Scoring, parsing, AI
│   │   └── utils/           # Auth utilities
│   ├── tests/               # pytest tests
│   ├── samples/             # Sample JD & resumes
│   ├── seed_data.py         # Demo data seeder
│   └── requirements.txt
├── frontend/
│   ├── app/                 # Next.js pages
│   ├── components/          # Reusable components
│   ├── lib/                 # API client, store, utils
│   └── package.json
├── SETUP.md                 # This file
└── README.md                # Project overview
```

## Troubleshooting

| Problem                      | Fix                                                  |
| ---------------------------- | ---------------------------------------------------- |
| `bcrypt` errors              | Ensure `bcrypt==4.0.1` in requirements.txt           |
| Frontend can't reach API     | Check `.env.local` has correct `NEXT_PUBLIC_API_URL` |
| Port already in use          | Kill the process or use a different port             |
| `sentence-transformers` slow | First run downloads the model (~80MB). Be patient.   |