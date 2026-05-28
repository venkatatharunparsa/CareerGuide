# job-agent

Agentic RAG job scraper: LangGraph agents, Playwright/BeautifulSoup scrapers, ChromaDB vector store, and a FastAPI backend.

## Structure

| Package   | Role                                      |
|-----------|-------------------------------------------|
| `backend` | FastAPI API, auth, scheduling, Gemini/RAG |
| `agents`  | LangGraph planner → scraper → monitor     |
| `scraper` | Site-specific and generic scrapers        |
| `rag`     | ChromaDB client, embeddings, collections  |
| `frontend`| React UI (scaffold separately)            |

## Quick start

**Full local setup (Docker, `.env`, UI, tests):** see **[LOCAL_SETUP.md](./LOCAL_SETUP.md)**.

```bash
copy .env.example .env   # Windows — edit and save keys
docker compose up -d
```

- **UI:** http://localhost:3000  
- **API:** http://localhost:8000/docs  

**Use Python 3.11** for non-Docker runs (matches `backend/Dockerfile`).

## Environment

See `.env.example` for all variables. Three Gemini API keys enable round-robin rotation on rate limits.
