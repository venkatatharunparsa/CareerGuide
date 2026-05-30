# Contributing to Job Agent

Thank you for your interest in contributing. This guide covers local setup, testing, and the pull request process.

---

## Local development setup

### Prerequisites

- Docker Desktop (recommended)
- Python 3.11+ (for running tests outside Docker)
- Git

### 1. Clone and configure

```bash
git clone https://github.com/YOUR_ORG/CareerGuide.git
cd CareerGuide/job-agent
cp .env.example .env
```

Edit `.env` and set:

- `SECRET_KEY` — any long random string
- At least one `GEMINI_API_KEY_*`
- `TAVILY_API_KEY` (recommended for full scraper coverage)

### 2. Start the stack

**Local Docker** (frontend talks to `http://localhost:8000`):

```bash
docker compose -f docker-compose.local.yml up --build -d
```

**Without Docker** (advanced):

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Separate terminal
cd frontend
npm install
npm run dev
```

Set `PYTHONPATH` to include the repo root so `agents/`, `scraper/`, and `rag/` import correctly:

```bash
export PYTHONPATH=/path/to/job-agent/backend:/path/to/job-agent
```

### 3. Verify the app

- Frontend: http://localhost:3000
- API docs: http://localhost:8000/docs
- Register a user, save a profile, run the agent from the Dashboard

---

## Running tests

The backend must be running on `http://localhost:8000` for integration tests.

```bash
pip install httpx   # if not already installed

# End-to-end smoke test (auth, profile, agent, jobs)
python test_smoke.py

# Full system test (profile, agent, scoring shape, resume tailor)
python test_full_system.py

# Individual scraper coverage
python test_scrapers_v2.py

# Data persistence across restarts
python test_persist.py
python test_persist.py after   # run after docker compose restart backend
```

All tests should report `PASS` or `ALL TESTS PASSED` before opening a PR.

### Rebuild after backend changes

```bash
docker compose -f docker-compose.local.yml build backend
docker compose -f docker-compose.local.yml up -d backend
```

### Rebuild after frontend changes

```bash
docker compose -f docker-compose.local.yml build frontend
docker compose -f docker-compose.local.yml up -d frontend
```

---

## Code style

- Match existing patterns in the file you edit (naming, imports, formatting).
- Keep changes focused — one feature or fix per PR.
- Do not commit secrets (`.env`, `*.pem`, API keys).
- Do not commit generated artifacts (`chroma_db/`, `*.db`, `node_modules/`).

---

## Submitting pull requests

1. **Fork** the repository on GitHub.
2. **Create a branch** from `main`:
   ```bash
   git checkout -b feature/short-description
   ```
3. **Make your changes** and test locally.
4. **Commit** with a clear message:
   ```bash
   git commit -m "Add scraper for example.com job board"
   ```
5. **Push** to your fork:
   ```bash
   git push origin feature/short-description
   ```
6. **Open a Pull Request** against `main` with:
   - What changed and why
   - How you tested it
   - Screenshots for UI changes (if applicable)

### PR checklist

- [ ] Tests pass locally (`python test_smoke.py`)
- [ ] No secrets or `.env` files in the diff
- [ ] `.env.example` updated if new environment variables were added
- [ ] README or CONTRIBUTING updated if setup steps changed

---

## Reporting issues

Open a GitHub issue with:

- Steps to reproduce
- Expected vs actual behavior
- Relevant logs (`docker compose logs backend --tail=50`)
- Your environment (OS, Docker version, local vs EC2)

---

## Questions

Open a GitHub Discussion or issue if you need help getting started.
