# CareerGuide — Job Agent (Full Project Guide)

> **One document to understand, run, and extend the project.**  
> Repository: [venkatatharunparsa/CareerGuide](https://github.com/venkatatharunparsa/CareerGuide.git)  
> Main application lives in the **`job-agent/`** folder.

---

## Table of contents

1. [What is this project?](#1-what-is-this-project)
2. [Key features](#2-key-features)
3. [How it works (high level)](#3-how-it-works-high-level)
4. [Tech stack](#4-tech-stack)
5. [Project structure](#5-project-structure)
6. [Prerequisites](#6-prerequisites)
7. [Quick start (Docker — recommended)](#7-quick-start-docker--recommended)
8. [Environment variables](#8-environment-variables)
9. [Using the application](#9-using-the-application)
10. [API reference](#10-api-reference)
11. [Agent pipeline (LangGraph)](#11-agent-pipeline-langgraph)
12. [Job scrapers](#12-job-scrapers)
13. [Database & storage](#13-database--storage)
14. [Running without Docker](#14-running-without-docker)
15. [Testing](#15-testing)
16. [Deployment (AWS)](#16-deployment-aws)
17. [Troubleshooting](#17-troubleshooting)
18. [Known limitations & tips](#18-known-limitations--tips)

---

## 1. What is this project?

**CareerGuide Job Agent** is an AI-powered career assistant that:

1. Builds a rich candidate profile (skills, roles, projects, experience, resume).
2. Runs an **agentic pipeline** (Planner → Scraper → Monitor) to find jobs from many sources.
3. **Scores each job** against your profile using Google Gemini (semantic match 0–100).
4. Lets you **bookmark jobs** and **generate ATS-tailored resume PDFs** per job.

It combines **LangGraph agents**, **RAG (ChromaDB)**, **multi-source web scraping**, and a **React + FastAPI** full-stack UI. The stack is containerized with **Docker Compose** and has been deployed to **AWS**.

---

## 2. Key features

| Feature | Description |
|--------|-------------|
| **User auth** | Register / login with JWT (Bearer token) |
| **Profile builder** | Skills, target roles, bio, experience years |
| **Resume upload** | PDF/DOCX parsing + automatic skill extraction (regex + Gemini) |
| **Projects & experience** | Structured entries; skills merged into master skill set |
| **AI job planner** | Gemini picks job boards, queries, company career pages |
| **Multi-source scraping** | 15+ boards + Tavily web search + India-specific sources |
| **Job matching** | Batch semantic scoring with skill gaps & learning suggestions |
| **Resume tailoring** | LaTeX-style content + PDF via ReportLab; ATS score |
| **Email digest** | Optional Gmail notification after agent run |
| **Vector memory** | ChromaDB stores profiles, job listings, career URLs |

---

## 3. How it works (high level)

```
┌─────────────┐     JWT      ┌──────────────────────────────────────────┐
│  React UI   │ ──────────►  │  FastAPI Backend (port 8000)             │
│  port 3000  │              │  /api/auth | profile | jobs | agents      │
└─────────────┘              └──────────────────┬───────────────────────┘
                                                │
                    POST /api/agents/run        ▼
                              ┌─────────────────────────────────────┐
                              │  LangGraph: Planner → Scraper → Monitor │
                              └─────────────────────────────────────┘
                                                │
              ┌─────────────────────────────────┼─────────────────────────┐
              ▼                                 ▼                         ▼
        Gemini 2.0 Flash                  ~20 scrapers              SQLite + ChromaDB
        (3-key rotation)                  (parallel async)          (persist results)
```

**Typical user flow:**

1. Register → log in  
2. **Profile** → add skills, roles, upload resume, add projects/experience → Save  
3. **Dashboard** → **Run Agent** (wait 1–3 minutes)  
4. **Jobs** → view ranked matches, bookmark, **Tailor Resume PDF**  

---

## 4. Tech stack

| Layer | Technologies |
|-------|----------------|
| **Backend** | FastAPI 0.111, Uvicorn, Python 3.11 |
| **Agents** | LangGraph 0.1.19, LangChain 0.2.5 |
| **LLM** | Google Gemini 2.0 Flash (`langchain-google-genai`) |
| **Vector DB** | ChromaDB 0.5.3 (cosine similarity) |
| **Relational DB** | SQLite (WAL mode) at `/chroma_db/jobagent.db` in Docker |
| **Scraping** | BeautifulSoup4, requests, Tavily API, site-specific modules |
| **Auth** | JWT (python-jose), bcrypt (passlib) |
| **Scheduling** | APScheduler (service exists; wire-up optional) |
| **Resume** | PyPDF2, python-docx, ReportLab, Gemini prompts |
| **Frontend** | React 18, Vite 5, React Router 6, TanStack Query, Tailwind CSS, axios |
| **Infra** | Docker Compose, named volume `chroma_data` |

---

## 5. Project structure

```
CareerGuide/
└── job-agent/                    ← Application root (run commands here)
    ├── .env                      ← Your secrets (create from .env.example)
    ├── .env.example
    ├── docker-compose.yml
    ├── LOCAL_SETUP.md            ← Shorter setup guide
    ├── README.md
    │
    ├── backend/                  ← FastAPI application
    │   ├── Dockerfile
    │   ├── requirements.txt
    │   └── app/
    │       ├── main.py           ← App entry, CORS, routers
    │       ├── config.py         ← Settings from .env
    │       ├── database.py       ← SQLite schema & CRUD
    │       ├── dependencies.py   ← JWT auth helpers
    │       ├── routers/
    │       │   ├── auth.py       ← Register, login, /me
    │       │   ├── profile.py    ← Profile, resume, projects, experience
    │       │   ├── jobs.py       ← List jobs, bookmark, tailor resume
    │       │   └── agents.py     ← Run agent, status
    │       ├── services/
    │       │   ├── gemini_service.py
    │       │   ├── profile_service.py
    │       │   ├── resume_service.py
    │       │   ├── email_service.py
    │       │   ├── rag_service.py
    │       │   └── scheduler_service.py
    │       └── utils/
    │           └── key_rotator.py
    │
    ├── agents/                   ← LangGraph pipeline
    │   ├── graph.py              ← Compiled graph + run_agent()
    │   ├── state.py              ← AgentState TypedDict
    │   ├── planner_agent.py
    │   ├── scraper_agent.py
    │   └── monitor_agent.py
    │
    ├── scraper/                  ← Job source integrations
    │   ├── base_scraper.py
    │   ├── tavily_job_scraper.py
    │   ├── naukri_scraper.py
    │   ├── internshala_scraper.py
    │   ├── google_jobs_scraper.py
    │   ├── india_jobs_scraper.py
    │   └── ... (see section 12)
    │
    ├── rag/                      ← ChromaDB client & collections
    │   ├── chroma_client.py
    │   ├── embeddings.py
    │   └── collections/
    │
    ├── frontend/                 ← React UI
    │   ├── Dockerfile
    │   ├── package.json
    │   └── src/
    │       ├── App.jsx
    │       ├── api/client.js
    │       └── pages/
    │           ├── Login.jsx
    │           ├── Dashboard.jsx
    │           ├── Profile.jsx
    │           └── Jobs.jsx
    │
    └── test_*.py                 ← Manual smoke / scraper tests
```

---

## 6. Prerequisites

| Requirement | Notes |
|-------------|--------|
| **Docker Desktop** | Recommended — runs backend + frontend together |
| **Git** | Clone the repository |
| **Python 3.11+** | Only if running tests or backend outside Docker |
| **Node.js 18+** | Only if running frontend outside Docker |

**Optional API keys** (app runs without them but with limited AI/search):

- **Gemini** — [Google AI Studio](https://aistudio.google.com/) (planner, scoring, resume)
- **Tavily** — [tavily.com](https://tavily.com) (live web job search, free tier)

---

## 7. Quick start (Docker — recommended)

All commands below are from the **`job-agent/`** directory.

### Step 1 — Clone and enter the project

```powershell
cd "C:\Users\THARUN PARSA\OneDrive\Documents\Projects\CareerGuide\job-agent"
```

(Use your actual path to `job-agent`.)

### Step 2 — Create environment file

```powershell
copy .env.example .env
```

Edit `.env` and set at minimum:

- `SECRET_KEY` — long random string (required for JWT)
- `GEMINI_API_KEY_1` — at least one Gemini key
- `TAVILY_API_KEY` — for live job search

**Save the file to disk** before starting Docker.

### Step 3 — Build and start

```powershell
docker compose build
docker compose up -d
```

### Step 4 — Verify

```powershell
docker compose ps
```

Expected:

- `job_agent_backend` — healthy  
- `job_agent_frontend` — up  

### Step 5 — Open the app

| Service | URL |
|---------|-----|
| **Frontend (UI)** | http://localhost:3000 |
| **Backend API** | http://localhost:8000 |
| **Swagger docs** | http://localhost:8000/docs |
| **Health check** | http://localhost:8000/health |

### Step 6 — First use

1. Open http://localhost:3000  
2. **Register** a new account  
3. Go to **Profile** → add skills & target roles → optionally upload resume → **Save**  
4. Go to **Dashboard** → click **Run Agent** (allow 1–3 minutes)  
5. Go to **Jobs** → review matches; try **Tailor Resume PDF** on a job  

---

## 8. Environment variables

Create `job-agent/.env` from `.env.example`:

| Variable | Required | Description |
|----------|----------|-------------|
| `SECRET_KEY` | **Yes** (prod) | JWT signing secret. Do not use default in production. |
| `GEMINI_API_KEY_1` | Recommended | Primary Gemini key |
| `GEMINI_API_KEY_2` | Optional | Second key for rate-limit rotation |
| `GEMINI_API_KEY_3` | Optional | Third key for rotation |
| `TAVILY_API_KEY` | Recommended | Tavily search for broad job discovery |
| `APP_ENV` | Optional | `development` (default) |
| `CHROMA_PERSIST_PATH` | Optional | `./chroma_db` locally; `/chroma_db` in Docker |
| `SQLITE_DB_PATH` | Docker | Set in compose: `/chroma_db/jobagent.db` |
| `FRONTEND_URL` | Optional | `http://localhost:3000` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Optional | Default `60` |
| `GMAIL_SENDER` | Optional | For email job digests |
| `GMAIL_APP_PASSWORD` | Optional | Gmail app password |
| `NOTIFICATION_EMAIL` | Optional | Where to send digests |

**Frontend (Docker):**

- `VITE_API_URL=http://localhost:8000` (set in `docker-compose.yml`)

**Note:** Without Gemini keys, the app uses **mock LLM responses**. Without Tavily, web-wide search is skipped; other scrapers may still return jobs.

---

## 9. Using the application

### Pages

| Page | Route | Purpose |
|------|-------|---------|
| **Login** | `/login` | Register or sign in |
| **Dashboard** | `/` | Profile summary, run agent, quick job preview |
| **Profile** | `/profile` | Skills, roles, resume, projects, experience |
| **Jobs** | `/jobs` | Matched jobs, scores, tailor resume, bookmarks |

### Profile tips

- **Skills** can be typed manually or extracted from resume upload.  
- **Projects** and **experience** auto-extract tech skills from descriptions.  
- Saving profile updates a **master skill set** (`all_skills`) used by the agent.  
- Agent run **requires at least one skill** (manual or from resume).

### Agent run

- Triggered from Dashboard: `POST /api/agents/run`  
- Timeout on frontend: **180 seconds**  
- Results are stored in SQLite (`evaluated_jobs`) and shown on Jobs page  
- If all scrapers fail, the system may fall back to **mock sample jobs** (for demo)

---

## 10. API reference

Base URL: `http://localhost:8000`  
Auth: `Authorization: Bearer <token>` (except register/login)

### Auth — `/api/auth`

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/register` | Body: `{ "username", "password" }` (password min 8 chars) |
| POST | `/token` | OAuth2 form: `username`, `password` → JWT |
| GET | `/me` | Current user (requires token) |

### Profile — `/api/profile`

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Full profile (skills, resumes, projects, experiences, `all_skills`) |
| POST | `/update` | Form: `skills`, `target_roles` (JSON strings), `experience_years`, `bio` |
| POST | `/resume/upload` | Multipart: `file`, `set_as_primary` |
| GET | `/resume/list` | List resumes |
| POST | `/resume/{id}/set-primary` | Set primary resume |
| DELETE | `/resume/{id}` | Delete resume |
| POST | `/project/add` | Form: name, description, tech_stack, url, role, outcome |
| GET | `/project/list` | List projects |
| DELETE | `/project/{id}` | Delete project |
| POST | `/experience/add` | Form: type, title, organization, description, skills, dates |
| GET | `/experience/list` | List experiences |
| DELETE | `/experience/{id}` | Delete experience |

### Jobs — `/api/jobs`

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | List evaluated jobs (sorted by match score) |
| POST | `/save` | Bookmark a job (JSON body) |
| GET | `/saved` | List bookmarked jobs |
| POST | `/tailor-resume/{job_index}` | Generate tailored PDF for job at index in evaluated list |

### Agents — `/api/agents`

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/run` | Run full LangGraph pipeline for current user |
| GET | `/status` | `{ has_results, job_count }` |

### Health

| Method | Endpoint | Response |
|--------|----------|----------|
| GET | `/health` | `{ "status": "ok", "env": "..." }` |

Interactive docs: **http://localhost:8000/docs**

---

## 11. Agent pipeline (LangGraph)

Defined in `agents/graph.py`:

```
planner → scraper → monitor → END
```

### Planner (`planner_agent.py`)

- Reads user profile: skills, roles, projects, experience, bio  
- Loads extra career URLs from ChromaDB (`career_urls` collection)  
- Asks **Gemini** to pick ~10 boards, per-site queries, company pages, alternative role titles  
- On failure: **rule-based fallback** using default boards  
- Output: `scrape_instructions` dict (per-URL config + `tavily_search` entry)

### Scraper (`scraper_agent.py`)

- Runs many scrapers **in parallel** via `asyncio.gather`  
- Deduplicates by job URL  
- If zero real jobs: uses **MOCK_JOBS** (5 sample listings)

### Monitor (`monitor_agent.py`)

- Evaluates up to 40 jobs in batches of 8 with **Gemini**  
- Scores 0–100; keeps jobs with score ≥ 45; returns top 25  
- Adds: `matched_skills`, `missing_skills`, `skill_gaps`, `learning_suggestions`  
- Saves to SQLite + ChromaDB `job_listings`  
- On Gemini failure: **keyword-based scoring** fallback  

### Gemini key rotation

- Up to 3 keys in `.env`  
- On 429 / quota / invalid key → rotate to next key  
- No keys → mock responses (limited functionality)

---

## 12. Job scrapers

Located in `job-agent/scraper/`. The scraper agent dispatches by URL/type:

| Scraper module | Sources / notes |
|----------------|-----------------|
| `tavily_job_scraper.py` | Web search across LinkedIn, Naukri, Indeed, etc. |
| `naukri_scraper.py` | naukri.com |
| `internshala_scraper.py` | internshala.com |
| `linkedin_rss_scraper.py` | LinkedIn jobs |
| `wellfound_scraper.py` | Wellfound / AngelList |
| `remoteok_scraper.py` | RemoteOK |
| `github_jobs_scraper.py` | Himalayas (via helper name) |
| `adzuna_scraper.py` | Arbeitnow |
| `company_career_scraper.py` | Direct company career pages |
| `google_jobs_scraper.py` | Google Jobs style search |
| `india_jobs_scraper.py` | Foundit, Unstop, Cutshort |
| `indeed_scraper.py` | Indeed |
| `jooble_scraper.py` | Jooble |
| `weworkremotely_scraper.py` | We Work Remotely |
| `playwright_scraper.py` | Dynamic pages (when used) |
| `bs4_scraper.py` | Generic BeautifulSoup |
| `adzuna_api_scraper.py` | Adzuna API |

**Default boards** (planner fallback list) include Naukri, Internshala, Indeed, RemoteOK, Wellfound, Shine, Glassdoor, Foundit, and others.

---

## 13. Database & storage

### SQLite tables (`database.py`)

| Table | Purpose |
|-------|---------|
| `users` | Username + hashed password |
| `user_profiles` | Skills, target roles, experience, bio |
| `resumes` | Uploaded resume text + extracted skills |
| `user_projects` | Project portfolio |
| `user_experiences` | Work / internship history |
| `job_cache` | Raw scraped jobs (per run) |
| `evaluated_jobs` | Scored/filtered jobs shown in UI |
| `saved_jobs` | User bookmarks |
| `tailored_resumes` | Generated resume history |

**Docker persistence:** volume `chroma_data` mounts at `/chroma_db` (SQLite + Chroma files).

### ChromaDB collections

| Collection | Purpose |
|------------|---------|
| `user_profiles` | Profile text for similarity search |
| `job_listings` | Evaluated job documents |
| `career_urls` | Company career pages per user |

---

## 14. Running without Docker

### Backend (Python 3.11)

From `job-agent/`:

```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r backend\requirements.txt
$env:PYTHONPATH = "$PWD;$PWD\backend"
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Ensure `.env` is in `job-agent/` root.

### Frontend

```powershell
cd frontend
npm install
npm run dev
```

- Vite dev server: http://localhost:5173 (or 3000 per config)  
- Proxy: `/api` → `http://localhost:8000`  
- Set `VITE_API_URL=http://localhost:8000` if not using proxy  

---

## 15. Testing

From `job-agent/` with Python 3.11+ and dependencies:

```powershell
pip install httpx python-dotenv beautifulsoup4 lxml tavily-python
```

| Script | Purpose |
|--------|---------|
| `python test_smoke.py` | Full API flow: register → profile → agent → jobs |
| `python test_tavily_quick.py` | Tavily search only |
| `python test_scrapers.py` | Individual scraper checks |
| `python test_scrapers_v2.py` | Extended scraper tests |
| `python test_full_system.py` | End-to-end system test |
| `python test_persist.py` | SQLite persistence check |

Expect smoke test to print `=== ALL TESTS PASSED ===` when backend is running.

---

## 16. Deployment (AWS)

The project has been deployed to AWS. Indicators in code:

- CORS allows `http://3.91.201.199:3000` and `http://3.91.201.199` in `backend/app/main.py`
- Recent commits mention post-AWS deployment scraper updates

**Typical production checklist:**

1. Set strong `SECRET_KEY` and real API keys in server `.env`  
2. Use `docker compose` or run containers on EC2  
3. Open ports **3000** (frontend) and **8000** (API) or put nginx in front  
4. Point `FRONTEND_URL` and CORS to your public domain/IP  
5. Back up Docker volume `chroma_data` for SQLite + Chroma data  

---

## 17. Troubleshooting

| Problem | Solution |
|---------|----------|
| Port 8000/3000 in use | Stop other apps or change ports in `docker-compose.yml` |
| Backend unhealthy | `docker logs job_agent_backend --tail 50` |
| Tavily returns 0 jobs | Set `TAVILY_API_KEY` in `.env`, `docker compose restart backend` |
| Agent returns 0 jobs | Save profile with skills first; check logs for scraper errors |
| Only mock jobs appear | All scrapers failed; check network/API keys |
| Register 400 | Username already exists — log in instead |
| Gemini errors | Valid keys in `.env`; invalid keys → mock mode |
| `.env` not loaded | File must be at `job-agent/` root; restart containers after edit |
| 401 on API calls | Token expired — log in again |
| Agent timeout in UI | Normal for slow scrapes; increase timeout or check backend logs |

**Health check (PowerShell):**

```powershell
Invoke-WebRequest -Uri http://localhost:8000/health -UseBasicParsing
```

**Verify Tavily in container:**

```powershell
docker exec job_agent_backend env | findstr TAVILY
```

### Useful Docker commands

```powershell
docker logs job_agent_backend --tail 50
docker logs -f job_agent_backend
docker compose restart backend
docker compose down
docker compose down -v    # WARNING: deletes chroma_data volume
```

---

## 18. Known limitations & tips

1. **Mock fallback** — If scraping and Gemini both fail partially, you may see demo jobs or mock LLM text. Always configure real API keys for production use.  
2. **Scraper reliability** — Job sites change HTML often; some scrapers may return 0 results until updated.  
3. **SQLite** — Fine for single-server deploy; not ideal for high concurrent write load.  
4. **Scheduler** — `SchedulerService` exists but is not started in `main.py` by default; periodic runs need wiring.  
5. **Security** — Change default `SECRET_KEY`; do not commit `.env` (already in `.gitignore`).  
6. **Resume PDF** — Tailored output is ReportLab-formatted text, not compiled LaTeX PDF from a TeX engine.  

---

## Quick checklist (copy for onboarding)

- [ ] Docker Desktop running  
- [ ] `job-agent/.env` created and saved (`SECRET_KEY`, Gemini, Tavily)  
- [ ] `docker compose up -d` from `job-agent/`  
- [ ] http://localhost:8000/health → OK  
- [ ] http://localhost:3000 loads  
- [ ] Registered account + profile saved with skills  
- [ ] Agent run completed → Jobs page shows listings  
- [ ] (Optional) `python test_smoke.py` passes  

---

## Related docs

- `job-agent/README.md` — Short overview  
- `job-agent/LOCAL_SETUP.md` — Step-by-step local setup  

---

**Maintainer note:** This file (`readmefortharun.md`) is the single onboarding document for the CareerGuide Job Agent. For questions about architecture or extending scrapers/agents, start with `agents/graph.py`, `backend/app/routers/agents.py`, and `scraper/scraper_agent.py` (via `agents/scraper_agent.py`).

*Last updated: May 2026*
