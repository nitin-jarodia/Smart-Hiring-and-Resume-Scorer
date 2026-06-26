# ScreenerAI: Technical Documentation and Analysis Report

## Project Overview
**ScreenerAI** is an intelligent, AI-powered Resume Screening & Hiring Platform designed to streamline the recruitment process. Traditional recruitment involves manually parsing hundreds of resumes to find suitable candidates—a process that is time-consuming, prone to human bias, and inefficient. ScreenerAI solves this problem by automating the initial stages of the hiring funnel using Artificial Intelligence and Natural Language Processing (NLP).

The platform facilitates a dual-sided ecosystem:
- **Recruiters** can post job descriptions, manage applications, view AI-generated candidate scores and insights, and seamlessly schedule interviews for shortlisted applicants.
- **Candidates** can upload their resumes, receive instant feedback via **Dynamic AI Tips**, integrate their **GitHub Profiles** for deeper project analysis, viewed through a comprehensive leaderboard.

AI acts as the core engine orchestrating these interactions, handling tasks that require semantic understanding such as scoring candidate fits, analyzing project value, and detecting resume embellishments. The system is built to be robust, recently overcoming critical schema synchronization issues to ensure 100% data integrity during applications.

---

## System Architecture
ScreenerAI follows a modern, decoupled client-server architecture:
- **Frontend (Client)**: A Next.js-based Single Page Application (SPA) interacting with the backend purely via RESTful APIs. It manages UI state, routing, and role-based views.
- **Backend (Server)**: A FastAPI Python backend that serves as the central orchestrator. It handles API requests, enforces business logic, delegates intensive AI tasks (like parsing and scoring), and communicates with the database.
- **Database Layer**: A relational database storing structured records for users, jobs, applications, and results.
- **AI/ML Modules**: Integrated locally within the backend pipeline. Upon resume upload, the backend triggers NLP sub-routines (e.g., SentenceTransformers) to parse text, compute embeddings, and detect specific patterns.

**High-Level Data Interaction**:
1. Client sends multipart form data (Resume PDF/Docx) to API.
2. API validates the request and passes the file to the Parsing Engine.
3. Extracted text flows into the AI Scorer, comparing it against Job Description vectors.
4. Results are serialized via Pydantic schemas and persisted to the SQL Database.
5. Client retrieves processed results dynamically to populate dashboards.

---

## Technology Stack

### Frontend
- **Framework**: Next.js (React) - Chosen for its robust router, SSR/SSG capabilities for performance, and excellent developer experience.
- **Styling**: Tailwind CSS & Vanilla CSS - Allows for rapid prototyping and maintaining a custom, premium, and responsive UI design system with dynamic glassmorphism and animations.
- **Icons**: Lucide React - Lightweight and modern icon set.

### Backend
- **Framework**: FastAPI (Python) - Exceptionally fast, inherently asynchronous, and natively integrates with Pydantic for robust request/response validation.
- **ORM**: SQLAlchemy - Provides a powerful abstraction layer for managing database relationships securely and reliably.

### Database
- **Engine**: SQLite - Used for local development and simplicity. Easily swappable to PostgreSQL or MySQL for production scalability.

### AI/ML Frameworks
- **Embeddings/NLP**: `sentence-transformers` (e.g., `all-MiniLM-L6-v2`) - Used to generate dense vector representations of text locally, without the cost or latency of external LLM APIs.
- **Text Processing**: Standard Python NLP practices, RegExp, and document parsers (`pdfplumber`, `docx2txt`) to handle varied document structures.

### Authentication & Security
- **Auth System**: Custom JWT (JSON Web Tokens) with hashed passwords (`bcrypt`). Simplifies stateless authentication between the Next.js client and FastAPI server.

---

## Core System Components

1. **User Authentication Module**: Handles signup, login, password hashing, and role determination (Admin/Recruiter vs. Candidate). 
2. **Candidate Dashboard**: A personalized portal showing the user's uploaded resumes, skill suggestions, market recommendations, AI-evaluated score, and tracked job applications.
3. **Recruiter Dashboard**: An interface for creating job postings, viewing aggregated pipeline analytics, and managing candidate applicants per job.
4. **Resume Upload and Parsing System**: Secures file uploads, rejects invalid formats, and utilizes specialized libraries to extract raw textual data and sections from diverse structural configurations (PDFs, Docs).
5. **Job Description Processing Module**: Parses defined required skills, nice-to-have skills, and the bulk text of a job posting to prepare it for comparison against incoming applications.
6. **Skill Extraction System**: Scans text arrays using pre-built technological dictionaries and NLP patterns to identify explicit frameworks, languages, and tools the candidate possesses.
7. **Resume Scoring Engine**: The brain of the application. It aggregates match percentages, computes semantic similarities, and calculates an overall quantitative score and qualitative confidence level.
8. **Semantic Similarity Model**: Calculates the distance between the vector representation of the JD and the candidate's experience.
9. **Interview Scheduling Module**: Allows recruiters to select a candidate and define date/time boundaries, creating `Interview` records mapping to specific applications.
10. **Project Quality Analyzer**: Maps candidate project descriptions to complexity levels and relevance. Now augmented by a **GitHub Profile Analyzer** that fetches star counts, languages, and repo descriptions for a more holistic engineering assessment.
11. **Resume Fraud Detection System**: Safeguards against common resume "hacking" tactics ensuring candidate integrity limits.
12. **Market Trend Recommendation System**: A continuous-learning proxy that advises candidates on missing, highly sought-after industry skills that pair intelligently with their existing skill stack.
13. **Dynamic Resume Review Engine**: A context-aware feedback module that generates personalized improvement tips by quoting actual sentences from the candidate's resume and suggesting specific rewrites.

---

## AI/ML Modules Detailed

- **Resume Parsing Logic**: Employs structural heuristics. It looks for header keywords (e.g., "Experience", "Education", "Projects") and visually formats parsed blocks by segmenting the text stream based on capitalization and line breaks.
- **Embedding Generation**: Text chunks are passed through a lightweight transformer model (like `MiniLM`). This creates vectors (lists of floats) capturing the contextual meaning of sentences, rather than just exact word matches.
- **Semantic Similarity Matching**: Performs a mathematical operation (Cosine Similarity) evaluating the angle between the Job Description embedding vector and the Candidate's Resume embedding vector. A higher score means closer semantic contextual alignment.
- **Candidate Ranking Algorithm**: Computes a weighted average factoring in:
    1. Exact skill match ratios (e.g., Required skills vs. Found skills).
    2. The semantic similarity cosine score.
    3. Seniority/Years of Experience overlap.
    4. Sub-module bonuses/penalties (Project Quality boosts, Fraud penalties).
- **Project Quality Analysis**: Extract text specifically categorized under "Projects". It evaluates the presence of action verbs, tech stack mentions within the project bounds, and quantified results (metrics/percentages) to classify the project's complexity level (Low, Medium, High).
- **Market Trend Analysis**: Maps a candidate's current capabilities against a predefined index of global high-demand skills (e.g., AI/ML, Cloud), isolating the delta and suggesting the most logical "next step" languages/tools.
- **GitHub Data Integration**: Candidates can link their GitHub profiles. The system fetches their top 3 most-starred repositories, extracting descriptions and languages to validate their engineering footprint and project impact.
- **Dynamic Heuristic Feedback**: Instead of boilerplate tips, the system identifies passive voice or missing metrics in specific bullet points and cites them directly (e.g., *"Instead of 'Developed X', try 'Architected X, resulting in 20% Y'..."*).

---

## Data Flow of the System

1. **Upload**: A Candidate uploads a resume via the `/candidate/dashboard` UI.
2. **Parsing**: The API saves the file locally, then invokes `extract_text()`, returning a structured dictionary of contact info and resume sections.
3. **JD Alignment**: The system pulls the target Job details (required skills, JD text).
4. **Scoring Execution**: The `score_resume()` pipeline runs sequentially: extracting skills -> semantic similarity generation -> project evaluation -> fraud detection.
5. **Database Persistence**: The generated analysis is compiled into a `Result` or `Application` entity and committed to the database.
6. **Feedback Loop**: The Candidate views their "match percent" and "skills to learn". The Recruiter views the candidate on the Job Applicants table, seeing the breakdown, flags, and aggregate score.
7. **Action**: The recruiter clicks to schedule an interview; an `Interview` record is spawned linking to the application ID.

---

## Database Design

The relational database is architected around the following key tables/collections utilizing SQLAlchemy:

- **Users**: Core authentication table holding email, hashed password, and role (`admin`, `recruiter`, `candidate`). One-to-one relationship with `CandidateProfile`.
- **CandidateProfile**: Stores candidate-specific data tied to the user (contact info, extracted skills, overall platform score).
- **Jobs**: Created by a Recruiter `User`. Holds JD text, requirements, company info. One-to-many relationship with `Applications` and `Resumes`.
- **Resumes**: Represents the physical document record. Links to `Jobs`.
- **Applications**: Mapped between `CandidateProfiles` and `Jobs`. Tracks the workflow state (`pending`, `shortlisted`, etc.) and the high-level match data.
- **Results**: Detailed granular AI breakdown per document submission (holds `breakdown`, `fraud_flags`, `project_evaluations`). 
- **Interviews**: Maps specifically to a `Result` or `Application` ID. Tracks `scheduled_at`, `duration`, and `meeting_link`.

---

## Features of the System

- **AI Resume Screening**: Fully automated reading and context-aware scoring of resumes against target positions.
- **Semantic Job Matching**: Going beyond ctrl+f keyword matches by understanding the true context of previous experience descriptors.
- **Skill Gap Analysis**: Highlighting specifically what a candidate lacks based on job parameters.
- **Project Evaluation**: Unique isolation and grading of side-projects, adding value for entry-level candidates.
- **Fraud Detection**: Active mitigation against ATS-manipulation strategies (keyword stuffing, invisible text).
- **Interview Scheduling**: Built-in modal scheduling linking candidates directly to the pipeline.
- **Recruiter Analytics**: Global metrics viewing active jobs, total processed resumes, and average score distributions.
- **Candidate Improvement Suggestions**: Giving actionable feedback directly to candidates based on pipeline failures.
- **Market Trend Recommendations**: Recommending popular lateral frameworks to improve candidate employability.

---

## Security and Validation

- **Authentication**: Secured via JWT access tokens. Tokens expire and validate user identity implicitly across all protected endpoints.
- **Authorization**: Role-based access control (RBAC) is implemented via FastAPI dependencies (`require_recruiter`, `require_candidate`). Thus, a candidate cannot fetch global recruiter stats or view competitor scores. Candidates are actively blinded from viewing hidden Recruiter insights like Fraud Flags.
- **Data Validation**: Pydantic schemas forcefully type-check input/output data (e.g., ensuring `min_years_exp` is an integer).
- **Password Protection**: Passwords are never stored in plaintext. They are inherently hashed using `bcrypt` salting.
- **Input Sanitization**: Database operations are routed through SQLAlchemy's parameterized queries, neutralizing SQL Injection vectors.

---

## Limitations of the Current System

- **Local Processing Bottlenecks**: Deep NLP calculations (like SentenceTransformers) run sequentially on the main server. Under heavy concurrent load (hundreds of resumes uploading at once), this CPU-bound process will heavily block FastAPI's event loop.
- **Parser Brittleness**: While `pdfplumber` works for most, highly complex, non-standard, or image-heavy PDFs might yield corrupted parsed texts leading to erroneous scores.
- **Scalability**: SQLite locks the database file on concurrent writes, meaning the system is strictly limited to low-traffic usage in its current state.

---

## Future Improvements

1. **Database Migration**: Swapping SQLite for PostgreSQL or MongoDB for enterprise-level scaling, concurrency, and complex JSON querying capabilities.
2. **Asynchronous Task Queue (Celery/Redis)**: Offloading the intensive AI scoring and parsing functions to background worker nodes, allowing the main API to remain blisteringly fast and accept uploads instantly.
3. **Advanced LLM Integration**: Transitioning from local heuristic reviews to full Generative AI (GPT-4/Claude) for conversational candidate summaries and complex sentiment analysis.
4. **Third-Party Integrations**: Connecting to Google Calendar APIs for real-time interview booking, and SendGrid for automated candidate email notifications.
5. **Advanced OCR Features**: Implementing Tesseract OCR to parse resume documents that are purely flattened images.

---

## Conclusion
ScreenerAI serves as a powerful demonstration of how targeted, embedded Artificial Intelligence implementations can drastically modernize traditional legacy workflows. By abstracting the repetitive, bias-prone nature of manual resume reading, it empowers recruiters to focus purely on human-to-human interview quality, while simultaneously empowering candidates with transparent feedback and growth metrics to better their careers. It bridges the divide between algorithmic efficiency and equitable hiring practices.
