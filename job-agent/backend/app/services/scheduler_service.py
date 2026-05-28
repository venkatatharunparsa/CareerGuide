import logging
from functools import lru_cache

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

logger = logging.getLogger(__name__)


class SchedulerService:
  """Background job scheduling for periodic agent runs."""

  def __init__(self) -> None:
    self._scheduler = AsyncIOScheduler()
    self._started = False

  def start(self) -> None:
    if self._started:
      return
    self._scheduler.start()
    self._started = True
    logger.info("APScheduler started")

  def shutdown(self) -> None:
    if self._started:
      self._scheduler.shutdown(wait=False)
      self._started = False
      logger.info("APScheduler shut down")

  def schedule_agent_run(
    self,
    user_id: str,
    job_func,
    *,
    hours: int = 24,
  ) -> None:
    self._scheduler.add_job(
      job_func,
      trigger=IntervalTrigger(hours=hours),
      id=f"agent_run_{user_id}",
      replace_existing=True,
      kwargs={"user_id": user_id},
    )
    logger.info("Scheduled agent run for user %s every %sh", user_id, hours)


@lru_cache
def get_scheduler_service() -> SchedulerService:
  return SchedulerService()
