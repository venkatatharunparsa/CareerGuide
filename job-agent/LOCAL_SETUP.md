# Run CareerGuide Job Agent Locally

Step-by-step guide to run the full stack on your machine (Windows, macOS, or Linux).

---

## What you need

| Requirement | Notes |
|-------------|--------|
| **Docker Desktop** | Recommended — runs backend + frontend together |
| **Python 3.11+** | Only if you run tests/scripts outside Docker |
| **Git** | To clone the repo |

Optional API keys (app still runs without them, with limited AI/search):

- **Gemini** — planner, job scoring, resume tailoring ([Google AI Studio](https://aistudio.google.com/))
- **Tavily** — live job search across the web ([tavily.com](https://tavily.com), free tier)

---

## 1. Get the project

```powershell
cd "C:\Users\YOUR_USER\OneDrive\Documents\Projects\CareerGuide\job-agent"
```

Use your actual path to the `job-agent` folder (repo root).

---

## 2. Configure environment variables

### 2.1 Create `.env`

```powershell
copy .env.example .env
```

### 2.2 Edit `.env` and set real values

Open `.env` in your editor and fill in:

```env
# Required for JWT auth
SECRET_KEY=your-long-random-secret-here

# Gemini (at least one key) — planner, scoring, resume tailor
GEMINI_API_KEY_1=your_gemini_key_here
GEMINI_API_KEY_2=
GEMINI_API_KEY_3=

# Tavily — live internet job search
TAVILY_API_KEY=your_tavily_key_here

# Optional — defaults are fine for local dev
APP_ENV=development
CHROMA_PERSIST_PATH=./chroma_db
FRONTEND_URL=http://localhost:3000
```

**Important:** Save the file to disk (Ctrl+S). Docker reads the file from disk, not unsaved editor buffers.

Do **not** use placeholder values like `your_tavily_key_here` in production; the app skips invalid placeholders for Tavily.

### Data persistence

Users, profiles, and job results are stored in **SQLite** at `/chroma_db/jobagent.db` (Docker volume `chroma_data`). Data survives `docker compose restart backend`. Run `python test_persist.py` then `python test_persist.py after` (after restart) to verify.

---

## 3. Start with Docker (recommended)

From the **repo root** (`job-agent/`):

### 3.1 First time or after dependency changes

```powershell
docker compose build
docker compose up -d
```

### 3.2 Everyday start

```powershell
docker compose up -d
```

### 3.3 Check containers

```powershell
docker compose ps
```

You should see:

- `job_agent_backend` — **healthy**
- `job_agent_frontend` — **Up**

### 3.4 Verify Tavily key is in the container

```powershell
docker exec job_agent_backend env | findstr TAVILY
```

You should see `TAVILY_API_KEY=...` (non-empty). On macOS/Linux use `grep` instead of `findstr`.

### 3.5 Open the app

| Service | URL |
|---------|-----|
| **Frontend (UI)** | http://localhost:3000 |
| **Backend API** | http://localhost:8000 |
| **API docs (Swagger)** | http://localhost:8000/docs |
| **Health check** | http://localhost:8000/health |

---

## 4. Use the app in the browser

1. Open http://localhost:3000  
2. **Register** a new account (or log in if you already registered).  
3. Go to **Profile** — add skills, target roles, experience; upload a resume (optional) → **Save**.  
4. Go to **Dashboard** → **Run Agent** (wait 1–2 minutes).  
5. Go to **Jobs** — review matches; use **Tailor Resume PDF** on a job if you saved a profile.  

---

## 5. Run automated tests (optional)

From repo root, with Python 3.11+ and network access:

```powershell
pip install httpx python-dotenv beautifulsoup4 lxml tavily-python
```

### Full API smoke test

```powershell
python test_smoke.py
```

Expect: `=== ALL TESTS PASSED ===` and jobs found after the agent step (may be 0–20 depending on scrapers).

### Tavily only

```powershell
python test_tavily_quick.py
```

### Scrapers (API + HTML)

```powershell
python test_scrapers.py
```

---

## 6. Useful Docker commands

```powershell
# View backend logs
docker logs job_agent_backend --tail 50

# Follow logs live
docker logs -f job_agent_backend

# Restart after .env or code changes
docker compose restart backend

# Rebuild backend image (after requirements.txt changes)
docker compose build backend
docker compose up -d

# Stop everything
docker compose down

# Stop and remove volumes (clears ChromaDB data)
docker compose down -v
```

---

## 7. Run backend without Docker (advanced)

Use **Python 3.11**. From repo root:

```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r backend\requirements.txt
$env:PYTHONPATH = "$PWD;$PWD\backend"
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Load `.env` from repo root (install `python-dotenv` or set variables manually).

Frontend separately:

```powershell
cd frontend
npm install
npm run dev
```

UI: http://localhost:5173 (Vite) — ensure `VITE_API_URL` points to http://localhost:8000

---

## 8. Troubleshooting

| Problem | What to do |
|---------|------------|
| **Port 8000 or 3000 in use** | Stop other apps or change ports in `docker-compose.yml` |
| **Backend unhealthy** | `docker logs job_agent_backend`; wait for Chroma first-time setup |
| **Tavily returns 0 jobs** | Save `TAVILY_API_KEY` in `.env`, run `docker compose restart backend` |
| **Agent returns 0 jobs** | Save profile first; check logs for `Real scrape succeeded`; re-run agent |
| **Register returns 400** | Username already exists — log in instead |
| **Smoke test register 400** | Normal if `smoketest` user exists; other steps should still pass |
| **Gemini errors** | Use valid keys in `.env`; invalid keys fall back to mock responses |
| **Docker not running** | Start Docker Desktop, then `docker compose up -d` |
| **`.env` not loaded** | File must be at repo root; confirm with `findstr TAVILY .env` (Windows) |

### Confirm API from PowerShell

```powershell
Invoke-WebRequest -Uri http://localhost:8000/health -UseBasicParsing
```

Status code should be **200**.

---

## 9. Project layout (reference)

```
job-agent/
├── .env                 # Your secrets (create from .env.example)
├── docker-compose.yml
├── backend/             # FastAPI app
├── agents/              # LangGraph planner → scraper → monitor
├── scraper/             # Job site + Tavily scrapers
├── rag/                 # ChromaDB
├── frontend/            # React UI
├── test_smoke.py
├── test_scrapers.py
└── test_tavily_quick.py
```

---

## 10. Quick checklist

- [ ] Docker Desktop running  
- [ ] `.env` created and **saved** with `SECRET_KEY`, Gemini, and Tavily keys  
- [ ] `docker compose up -d`  
- [ ] http://localhost:8000/health returns OK  
- [ ] http://localhost:3000 loads  
- [ ] Profile saved → Agent run → Jobs page shows listings  
- [ ] (Optional) `python test_smoke.py` passes  

Once this checklist is green, local development is ready. Next step: AWS deployment.
