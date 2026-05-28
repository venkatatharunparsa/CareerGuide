import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routers import agents
from app.routers import auth
from app.routers import jobs
from app.routers import profile

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
settings = get_settings()

app = FastAPI(title="Job Agent API", version="1.0.0", docs_url="/docs")

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

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(profile.router, prefix="/api/profile", tags=["profile"])
app.include_router(jobs.router, prefix="/api/jobs", tags=["jobs"])
app.include_router(agents.router, prefix="/api/agents", tags=["agents"])


@app.on_event("startup")
async def startup():
  from app.database import init_db

  init_db()
  logger.info("SQLite database initialized")

  try:
    from rag.chroma_client import ChromaDBClient

    ChromaDBClient()
    logger.info("ChromaDB initialized")
  except Exception as e:
    logger.warning("ChromaDB startup warning (non-fatal): %s", e)


@app.get("/health")
async def health():
  return {"status": "ok", "env": settings.app_env}
