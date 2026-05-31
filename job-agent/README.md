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

## Architecture

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

1. **Planner** — reads the full user profile, picks job boards, builds search keywords, configures Tavily queries via Gemini (rule-based fallback on quota errors).
2. **Scraper** — runs all sources in parallel. Deduplicates by MD5 job hash. Caches raw results in SQLite.
3. **Monitor / Evaluator** — batch-scores jobs 0–100 with Gemini (keyword fallback). Persists top matches with skill gaps to SQLite and ChromaDB.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Agent orchestration | LangGraph + LangChain |
| LLM | Google Gemini 1.5 Flash (3-key rotation) |
| Web search | Tavily API |
| Backend | FastAPI + Python 3.11 |
| Database | SQLite (persistent) + ChromaDB (RAG) |
| Frontend | React 18 + Vite + TailwindCSS |
| Scraping | httpx + BeautifulSoup4 + JSON-LD extraction |
| PDF | ReportLab + LaTeX templates |
| Scheduler | APScheduler (6-hour auto-run) |
| Deployment | Docker + Nginx + AWS EC2 |
| CI/CD | GitHub Actions |

---

## Quick Start (Local)

### Prerequisites

- Docker Desktop installed
- Git installed
- 3 free Gemini API keys ([aistudio.google.com](https://aistudio.google.com))
- 1 free Tavily API key ([tavily.com](https://tavily.com))

### Step 1 — Fork and clone

```bash
# Fork the repo on GitHub first, then:
git clone https://github.com/YOUR_USERNAME/job-agent.git
cd job-agent
```

### Step 2 — Configure environment

```bash
cp .env.example .env
```

Open `.env` and fill in:

```env
GEMINI_API_KEY_1=AIzaSy...     # From aistudio.google.com
GEMINI_API_KEY_2=AIzaSy...     # Second account (avoids quota)
GEMINI_API_KEY_3=AIzaSy...     # Third account (failsafe)
TAVILY_API_KEY=tvly-...        # From tavily.com
SECRET_KEY=run-python-secrets-token-hex-32-here
```

Generate `SECRET_KEY`:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### Step 3 — Run

```bash
docker compose -f docker-compose.local.yml up --build -d
```

First build takes 5–10 minutes. Then open:

- Frontend: http://localhost:3000
- API docs: http://localhost:8000/docs

> **Note:** Use `docker-compose.local.yml` for local dev so `VITE_API_URL` points to `http://localhost:8000`. For EC2/production, use `docker compose up --build -d` (see [Deploy to AWS](#deploy-to-aws-free-tier-247)).

### Step 4 — Set up your profile

1. Register an account at http://localhost:3000
2. Go to **Profile**
3. Upload your resume PDF — skills auto-extracted
4. Add projects with tech stacks
5. Add work experience / internships
6. Set target roles
7. Click **Save**

### Step 5 — Run the agent

1. Go to **Dashboard**
2. Click **Run Job Agent**
3. Wait 60–90 seconds
4. Go to **Jobs** — see ranked matches
5. Click any job → see matched/missing skills
6. Click **Tailor Resume PDF** → download ATS resume

---

## Deploy to AWS Free Tier (24/7)

### Step 1 — Launch EC2

1. Go to AWS Console → EC2 → Launch Instance
2. Choose: Ubuntu 22.04 or Amazon Linux 2023
3. Type: **t3.micro** (free tier)
4. Create key pair → download `.pem` file
5. Security group: allow ports **22**, **80**, **8000**, **3000**
6. Launch

### Step 2 — Connect and install Docker

```bash
ssh -i "your-key.pem" ec2-user@YOUR_EC2_IP

sudo yum update -y
sudo yum install -y docker git
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.24.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Install buildx
mkdir -p ~/.docker/cli-plugins
curl -SL "https://github.com/docker/buildx/releases/download/v0.17.1/buildx-v0.17.1.linux-amd64" -o ~/.docker/cli-plugins/docker-buildx
chmod +x ~/.docker/cli-plugins/docker-buildx
```

Log out and back in so the `docker` group applies.

### Step 3 — Clone and configure

```bash
git clone https://github.com/YOUR_USERNAME/job-agent.git
cd job-agent
nano .env   # Add your real API keys
```

Update `FRONTEND_URL` in `.env`:

```env
FRONTEND_URL=http://YOUR_EC2_IP:3000
```

Update `VITE_API_URL` in `docker-compose.yml` (baked at frontend **build** time):

```bash
sed -i 's|VITE_API_URL=http://3.91.201.199:8000|VITE_API_URL=http://YOUR_EC2_IP:8000|g' docker-compose.yml
```

Add GitHub Actions secrets for auto-deploy: `EC2_HOST`, `EC2_USER`, `EC2_SSH_KEY` (see `.github/workflows/deploy.yml`).

### Step 4 — Deploy

```bash
docker-compose up --build -d
docker-compose logs -f backend
# Wait for: Application startup complete
```

### Step 5 — Auto-restart on reboot

```bash
sudo nano /etc/systemd/system/job-agent.service
```

Paste:

```ini
[Unit]
Description=Job Agent
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/home/ec2-user/job-agent
ExecStart=/usr/local/bin/docker-compose up -d
ExecStop=/usr/local/bin/docker-compose down

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable job-agent
```

### AWS Free Tier cost: $0/month

- EC2 t3.micro: 750h free
- EBS storage: 30GB free
- Gemini API: free tier (3 keys)
- Tavily: 1000 searches/month free
- Gmail SMTP: always free

---

## Email Notifications Setup

Get Gmail App Password:

1. [myaccount.google.com](https://myaccount.google.com)
2. Security → 2-Step Verification → App Passwords
3. Create "Job Agent" → copy 16-char password

Add to `.env`:

```env
GMAIL_SENDER=your@gmail.com
GMAIL_APP_PASSWORD=xxxx xxxx xxxx xxxx
NOTIFICATION_EMAIL=your@gmail.com
```

You will receive a digest email every 6 hours with:

- Job title and company
- Match percentage
- Direct apply link

---

## Environment Variables Reference

| Variable | Required | Description |
|---|---|---|
| `GEMINI_API_KEY_1` | Yes | Gemini API key ([aistudio.google.com](https://aistudio.google.com)) |
| `GEMINI_API_KEY_2` | Recommended | Second key for rotation |
| `GEMINI_API_KEY_3` | Recommended | Third key for failsafe |
| `TAVILY_API_KEY` | Yes | Tavily search API ([tavily.com](https://tavily.com)) |
| `SECRET_KEY` | Yes | JWT secret (generate randomly) |
| `ALGORITHM` | No | JWT algorithm (default: `HS256`) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | No | Token expiry (default: `60`) |
| `CHROMA_PERSIST_PATH` | No | ChromaDB path (default: `/chroma_db`) |
| `SQLITE_DB_PATH` | No | SQLite path (default: `/chroma_db/jobagent.db`) |
| `APP_ENV` | No | `development` or `production` |
| `FRONTEND_URL` | Yes | Frontend URL for CORS |
| `GMAIL_SENDER` | No | Gmail address for notifications |
| `GMAIL_APP_PASSWORD` | No | Gmail app password |
| `NOTIFICATION_EMAIL` | No | Where to send digests |

**Frontend (Docker build-time):** `VITE_API_URL` is set in `docker-compose.yml` or `docker-compose.local.yml` under `frontend.build.args` — not read from `.env` at runtime.

See [`.env.example`](./.env.example) for commented templates.

---

## Known Limitations

We are honest about what does not work perfectly yet. These are areas where contributors can make the biggest impact:

### Scraping (HIGH PRIORITY)

- LinkedIn, Indeed, Naukri block simple HTTP scrapers — returns 0 jobs without Tavily fallback
- Google Jobs HTML structure changes frequently
- Foundit and Cutshort selectors break regularly
- No Playwright integration yet for JS-heavy sites (blocked by 1GB RAM constraint on free EC2)

### AI / Scoring

- Gemini free tier quota exhausts quickly with 3+ users — falls back to keyword matching
- Resume tailoring quality drops without real resume text uploaded
- LaTeX compilation not available — uses ReportLab instead (PDF looks plain, not like a proper LaTeX resume)

### Features Not Yet Built

- Auto-apply to jobs (coming next)
- LinkedIn OAuth integration
- Multiple user support with isolated scheduling
- Resume version history
- Job application tracking
- Browser extension for one-click apply
- Mobile app

### Infrastructure

- No HTTPS/SSL yet (running on HTTP)
- No load balancing (single EC2 instance)
- No database backups automated
- Frontend rebuilds required when EC2 IP changes

---

## Contributing

We welcome contributions. See [CONTRIBUTING.md](./CONTRIBUTING.md) for the full guide.

### High-priority areas

1. **Scraper reliability** — Playwright sidecar, better selectors, anti-bot bypass, more Indian boards
2. **Resume quality** — LaTeX compilation (tectonic/pdflatex), more templates, browser preview
3. **Semantic scoring** — prompt tuning, Ollama/local LLM option, embedding-based similarity
4. **Multi-user scheduling** — per-user cron, timezone-aware runs, rate limiting

### Quick contribution flow

```bash
git clone https://github.com/YOUR_USERNAME/job-agent.git
cd job-agent
git checkout -b feat/your-feature-name
# make changes
python test_smoke.py
git push origin feat/your-feature-name
# open Pull Request against main
```

---

## Project Structure

```
job-agent/
├── backend/                 FastAPI app (auth, profile, jobs, agents)
├── agents/                  LangGraph planner, scraper, monitor nodes
├── scraper/                 Per-site scrapers + JSON-LD utilities
├── rag/                     ChromaDB client
├── frontend/                React SPA (Vite + Tailwind)
├── docker-compose.yml       EC2 / production
├── docker-compose.local.yml   Local development
├── .github/workflows/       CI/CD (deploy to EC2)
├── test_smoke.py            End-to-end smoke test
└── test_scrapers_v2.py      Scraper coverage test
```

---

## Testing

```bash
# Backend must be running on localhost:8000
python test_smoke.py
python test_full_system.py
python test_scrapers_v2.py
```

---

## License

[MIT](./LICENSE)
