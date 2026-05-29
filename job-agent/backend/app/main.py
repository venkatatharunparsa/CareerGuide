from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings

logging.basicConfig(
  level=logging.INFO,
  format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
  """Modern FastAPI lifespan handler — replaces deprecated on_event."""
  # ── STARTUP ──────────────────────────────────
  logger.info("Starting Job Agent API...")

  # 1. Initialize SQLite
  try:
    from app.database import init_db

    init_db()
    logger.info("SQLite initialized")
  except Exception as e:
    logger.error("SQLite init failed: %s", e)

  # 2. Initialize ChromaDB
  try:
    from rag.chroma_client import ChromaDBClient

    ChromaDBClient()
    logger.info("ChromaDB initialized")
  except Exception as e:
    logger.warning("ChromaDB init warning (non-fatal): %s", e)

  # 3. Start background scheduler
  try:
    from app.services.scheduler_service import start_scheduler

    start_scheduler()
    logger.info("APScheduler started — runs every 6 hours")
  except Exception as e:
    logger.warning("Scheduler init failed (non-fatal): %s", e)

  logger.info("Job Agent API ready")
  yield

  # ── SHUTDOWN ─────────────────────────────────
  logger.info("Shutting down Job Agent API...")
  try:
    from app.services.scheduler_service import scheduler

    if scheduler.running:
      scheduler.shutdown(wait=False)
      logger.info("Scheduler stopped")
  except Exception:
    pass


app = FastAPI(
  title="Job Agent API",
  version="2.0.0",
  docs_url="/docs",
  lifespan=lifespan,
)

app.add_middleware(
  CORSMiddleware,
  allow_origins=[
    "http://localhost:3000",
    "http://localhost:5173",
    "http://3.91.201.199:3000",
    "http://3.91.201.199",
    settings.frontend_url,
  ],
  allow_credentials=True,
  allow_methods=["*"],
  allow_headers=["*"],
)

from app.routers import agents, auth, jobs, profile

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(profile.router, prefix="/api/profile", tags=["profile"])
app.include_router(jobs.router, prefix="/api/jobs", tags=["jobs"])
app.include_router(agents.router, prefix="/api/agents", tags=["agents"])


@app.get("/health")
async def health():
  return {
    "status": "ok",
    "env": settings.app_env,
    "version": "2.0.0",
  }
