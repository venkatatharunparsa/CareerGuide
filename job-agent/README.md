# Job Agent

An agentic job search platform that scrapes listings from dozens of sources, scores them against your profile with AI, and tailors ATS-optimized resumes for each role.

**Live demo:** [http://3.91.201.199:3000](http://3.91.201.199:3000)

---

## Features

- **Rich user profiles** — skills, projects, work experience, resume upload with automatic skill extraction
- **Multi-source job scraping** — RemoteOK, Himalayas, Arbeitnow, Tavily web search, Google Jobs, India boards (Foundit, Unstop, Cutshort), LinkedIn RSS, Naukri, and more
- **LangGraph agent pipeline** — planner → parallel scraper → semantic evaluator with keyword fallback
- **AI job matching** — match scores, matched/missing skills, skill gaps, and learning suggestions per job
- **ATS resume tailoring** — LaTeX templates, Gemini-generated content, PDF export with ATS score feedback
- **Vector memory** — ChromaDB stores profiles and job listings for semantic retrieval
- **Email digests** — optional Gmail notifications after each agent run
- **Background scheduler** — APScheduler auto-scrapes every 6 hours for active users
- **Docker-first** — one-command deploy for local dev or AWS EC2

---

## Quick start

### Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (recommended)
- Git

### 1. Clone and configure

```bash
git clone https://github.com/YOUR_ORG/CareerGuide.git
cd CareerGuide/job-agent
cp .env.example .env   # Windows: copy .env.example .env
```

Edit `.env` and set at least `SECRET_KEY` and one `GEMINI_API_KEY_*`. See [Environment variables](#environment-variables).

### 2. Run with Docker

**Local development** (API at `localhost:8000`):

```bash
docker compose -f docker-compose.local.yml up --build -d
```

**Production / EC2** (uses public API URL baked into the frontend build):

```bash
docker compose up --build -d
```

### 3. Open the app

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| API docs | http://localhost:8000/docs |
| Health | http://localhost:8000/health |

Register a user, fill in your profile, then run the agent from the Dashboard.

---

## Environment variables

Copy `.env.example` to `.env`. Variables are loaded by the backend via `env_file` in Docker Compose.

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GEMINI_API_KEY_1` | Recommended | — | Primary Google Gemini API key ([AI Studio](https://aistudio.google.com/)) |
| `GEMINI_API_KEY_2` | Optional | — | Second key for rate-limit rotation |
| `GEMINI_API_KEY_3` | Optional | — | Third key for rate-limit rotation |
| `TAVILY_API_KEY` | Recommended | — | Tavily search API ([tavily.com](https://tavily.com)) for internet-wide job discovery |
| `SECRET_KEY` | **Yes** | — | JWT signing secret — use a long random string in production |
| `ALGORITHM` | No | `HS256` | JWT algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | No | `60` | Auth token lifetime in minutes |
| `APP_ENV` | No | `development` | Environment label (`development` / `production`) |
| `CHROMA_PERSIST_PATH` | No | `./chroma_db` | ChromaDB storage path |
| `SQLITE_DB_PATH` | No | `/chroma_db/jobagent.db` | SQLite database path (set in Docker Compose) |
| `BACKEND_HOST` | No | `0.0.0.0` | FastAPI bind host |
| `BACKEND_PORT` | No | `8000` | FastAPI port |
| `FRONTEND_URL` | No | `http://localhost:3000` | CORS allowed origin for the React app |
| `GMAIL_SENDER` | Optional | — | Gmail address for job digest emails |
| `GMAIL_APP_PASSWORD` | Optional | — | Gmail app password (not your login password) |
| `NOTIFICATION_EMAIL` | Optional | — | Recipient for job digest emails |

**Frontend (Docker build-time only):** `VITE_API_URL` is baked into the React bundle at **image build** time. Set it in `docker-compose.yml` (`build.args`) for EC2, or `docker-compose.local.yml` for local dev. It is not read from `.env` at runtime by Vite.

---

## Architecture

Job Agent is a three-tier system: React frontend, FastAPI backend, and a LangGraph agent pipeline with pluggable scrapers.

```
┌─────────────┐     REST/JWT      ┌──────────────────┐
│  React UI   │ ◄──────────────► │  FastAPI Backend │
│  (Vite)     │                  │  SQLite + Auth   │
└─────────────┘                  └────────┬─────────┘
                                          │
                         ┌────────────────┼────────────────┐
                         ▼                ▼                ▼
                  ┌────────────┐   ┌────────────┐   ┌────────────┐
                  │ LangGraph  │   │  ChromaDB  │   │ APScheduler│
                  │  Agents    │   │  (vectors) │   │  (6h cron) │
                  └─────┬──────┘   └────────────┘   └────────────┘
                        │
          ┌─────────────┼─────────────┐
          ▼             ▼             ▼
     ┌─────────┐  ┌──────────┐  ┌─────────┐
     │ Planner │→ │ Scraper  │→ │ Monitor │
     │ (Gemini)│  │ (parallel│  │(scoring)│
     └─────────┘  │ sources) │  └─────────┘
                  └──────────┘
```

**Agent flow**

1. **Planner** — reads the full user profile (skills, projects, experience), picks job boards, builds search keywords, and configures Tavily queries via Gemini (with rule-based fallback).
2. **Scraper** — runs all sources in parallel (API scrapers, Tavily, Google Jobs, India boards, company career pages). Deduplicates by MD5 job hash. Caches raw results in SQLite.
3. **Monitor / Evaluator** — batch-scores jobs 0–100 with Gemini (keyword fallback on quota limits). Persists top matches with skill gaps and learning suggestions to SQLite and ChromaDB.

**Data stores**

- **SQLite** — users, profiles, resumes, projects, experiences, job cache, evaluated jobs, tailored resumes
- **ChromaDB** — semantic embeddings for profiles, job listings, and career page URLs

---

## Tech stack

| Layer | Technologies |
|-------|----------------|
| Frontend | React 18, Vite, Tailwind CSS, TanStack Query, Axios |
| Backend | FastAPI, Pydantic, python-jose, SQLite |
| Agents | LangGraph, LangChain, Google Gemini 2.0 Flash |
| Scraping | httpx, BeautifulSoup, Tavily, Playwright (memory-safe config) |
| Vector DB | ChromaDB |
| PDF / Resume | ReportLab, LaTeX templates via Gemini |
| Scheduling | APScheduler |
| Deploy | Docker Compose, GitHub Actions → EC2 |

---

## Project structure

```
job-agent/
├── backend/          FastAPI app (auth, profile, jobs, agents routers)
├── agents/           LangGraph planner, scraper, monitor nodes
├── scraper/          Per-site scrapers + JSON-LD base utilities
├── rag/              ChromaDB client
├── frontend/         React SPA
├── docker-compose.yml           EC2 / production
├── docker-compose.local.yml     Local development
└── test_smoke.py     End-to-end smoke test
```

---

## Testing

```bash
# Backend must be running on localhost:8000
python test_smoke.py
python test_full_system.py
python test_scrapers_v2.py
```

See [CONTRIBUTING.md](./CONTRIBUTING.md) for full development setup.

---

## Contributing

We welcome issues and pull requests. Please read [CONTRIBUTING.md](./CONTRIBUTING.md) before submitting changes.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/my-change`)
3. Commit your changes
4. Push and open a Pull Request against `main`

---

## License

[MIT](./LICENSE)
