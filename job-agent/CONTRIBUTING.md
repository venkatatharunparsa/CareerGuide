# Contributing to Job Agent

Thank you for your interest in contributing. This guide covers local setup, testing, and the pull request process.

---

## High-priority issues

### 1. Scraper reliability

The biggest weakness. We need:

- Playwright scraper container (separate Docker service)
- Better HTML selector maintenance for Naukri/Indeed
- Anti-bot bypass strategies
- More Indian job boards (Freshersworld, Hirist, iimjobs)

### 2. Resume quality

- LaTeX compilation via tectonic or pdflatex in Docker
- More resume templates (5+ professional designs)
- ATS score validation against real ATS systems
- Resume preview in browser before download

### 3. Semantic scoring accuracy

- Better prompt engineering for Gemini scoring
- Local LLM option (Ollama) for offline/quota-free use
- Embedding-based similarity as scoring layer

### 4. Multi-user scheduling

- Per-user cron configuration
- Timezone-aware scheduling
- Rate limiting per user

---

## Local development setup

### Prerequisites

- Docker Desktop (recommended)
- Python 3.11+ (for running tests outside Docker)
- Git
- 3 Gemini API keys + 1 Tavily key (free tiers)

### Clone and configure

```bash
git clone https://github.com/YOUR_USERNAME/job-agent.git
cd job-agent
cp .env.example .env
```

Edit `.env` and set `SECRET_KEY`, `GEMINI_API_KEY_*`, and `TAVILY_API_KEY`.

Generate `SECRET_KEY`:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### Run locally

```bash
docker compose -f docker-compose.local.yml up --build -d
```

- Frontend: http://localhost:3000
- API docs: http://localhost:8000/docs

### Run tests

```bash
pip install httpx

python test_smoke.py
python test_scrapers_v2.py
python test_full_system.py
python test_persist.py
```

Watch logs:

```bash
docker compose logs -f backend
```

### Rebuild after changes

```bash
# Backend
docker compose -f docker-compose.local.yml build backend
docker compose -f docker-compose.local.yml up -d backend

# Frontend
docker compose -f docker-compose.local.yml build frontend
docker compose -f docker-compose.local.yml up -d frontend
```

---

## Submitting pull requests

1. Fork the repository on GitHub
2. Clone your fork and create a branch:
   ```bash
   git clone https://github.com/YOUR_USERNAME/job-agent.git
   cd job-agent
   git checkout -b feat/your-feature-name
   ```
3. Make your changes with tests
4. Run `python test_smoke.py` — must pass
5. Push and open a Pull Request against `main`

### PR checklist

- [ ] `python test_smoke.py` passes
- [ ] No secrets (`.env`, `*.pem`) in the diff
- [ ] `.env.example` updated if new env vars were added
- [ ] README updated if setup or behavior changed

---

## Code style

- Match existing patterns in the file you edit
- Keep changes focused — one feature or fix per PR
- Do not commit generated artifacts (`chroma_db/`, `*.db`, `node_modules/`)

---

## Reporting issues

Open a GitHub issue with:

- Steps to reproduce
- Expected vs actual behavior
- Relevant logs: `docker compose logs backend --tail=50`
- Environment (OS, Docker version, local vs EC2)
