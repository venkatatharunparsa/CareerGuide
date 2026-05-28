import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.database import cache_jobs, get_evaluated_jobs, get_full_profile, save_evaluated_jobs
from app.dependencies import get_current_username

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/run")
async def run_agent(username: Annotated[str, Depends(get_current_username)]):
  try:
    from agents.graph import run_agent as graph_run

    profile = get_full_profile(username)
    if not profile.get("skills") and not profile.get("all_skills"):
      raise HTTPException(
        status_code=400,
        detail="Save your profile with skills first.",
      )

    result = await graph_run(
      user_id=username,
      user_profile=profile,
      target_roles=profile.get("target_roles", []),
    )

    filtered = result.get("filtered_jobs", [])

    try:
      cache_jobs(username, result.get("scraped_jobs", []))
    except Exception:
      pass

    save_evaluated_jobs(username, filtered)

    try:
      from app.services.email_service import get_email_service

      get_email_service().send_job_digest(filtered, username)
    except Exception:
      pass

    updates = result.get("monitoring_updates", [])
    return {
      "status": result.get("status", "complete"),
      "total_jobs": len(filtered),
      "avg_score": (
        int(sum(j.get("match_score", 0) for j in filtered) / len(filtered))
        if filtered
        else 0
      ),
      "sites_scraped": len(result.get("scrape_instructions", {})),
      "summary": updates[0] if updates else "Complete.",
      "jobs": filtered,
    }
  except HTTPException:
    raise
  except Exception as e:
    logger.exception("Agent run failed")
    raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/status")
async def agent_status(username: Annotated[str, Depends(get_current_username)]):
  jobs = get_evaluated_jobs(username)
  return {"has_results": bool(jobs), "job_count": len(jobs)}
