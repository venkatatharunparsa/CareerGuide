import asyncio
import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

logger = logging.getLogger(__name__)
scheduler = AsyncIOScheduler(
  job_defaults={
    "coalesce": True,
    "max_instances": 1,
    "misfire_grace_time": 300,
  }
)


def start_scheduler():
  if scheduler.running:
    logger.info("Scheduler already running")
    return

  scheduler.add_job(
    _run_scheduled_agents,
    trigger=IntervalTrigger(hours=6),
    id="auto_scrape",
    replace_existing=True,
    name="Auto Job Scrape",
  )
  scheduler.start()
  logger.info("Scheduler started — auto-scrape every 6h")


async def _run_scheduled_agents():
  """Run agent for all users with saved profiles."""
  logger.info("Scheduled agent run starting...")
  try:
    users = await asyncio.to_thread(_get_active_users)
    if not users:
      logger.info("No active users to process")
      return

    logger.info("Running scheduled scrape for %d users", len(users))

    from agents.graph import run_agent
    from app.database import get_full_profile, save_evaluated_jobs
    from app.services.email_service import get_email_service

    email_svc = get_email_service()

    for username in users:
      try:
        profile = await asyncio.to_thread(get_full_profile, username)
        if not profile or not profile.get("skills"):
          continue

        result = await run_agent(
          user_id=username,
          user_profile=profile,
          target_roles=profile.get("target_roles", []),
        )

        jobs = result.get("filtered_jobs", [])

        await asyncio.to_thread(save_evaluated_jobs, username, jobs)

        if jobs:
          email_svc.send_job_digest(jobs, username)
          logger.info("Scheduled run done for %s: %d jobs", username, len(jobs))

      except Exception as e:
        logger.error("Scheduled run failed for %s: %s", username, e)

  except Exception as e:
    logger.error("Scheduler error: %s", e)


def _get_active_users() -> list:
  """Synchronous DB query — called via asyncio.to_thread."""
  try:
    from app.database import get_db

    conn = get_db()
    rows = conn.execute(
      "SELECT username FROM user_profiles "
      "WHERE skills != '[]' AND skills IS NOT NULL"
    ).fetchall()
    conn.close()
    return [r["username"] for r in rows]
  except Exception as e:
    logger.error("Failed to get active users: %s", e)
    return []
