import base64
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.database import get_evaluated_jobs, get_full_profile, get_saved_jobs, save_job_bookmark
from app.dependencies import get_current_username

router = APIRouter()


@router.get("/")
async def list_jobs(username: Annotated[str, Depends(get_current_username)]):
  return get_evaluated_jobs(username)


@router.post("/save")
async def bookmark_job(
  job: dict,
  username: Annotated[str, Depends(get_current_username)],
):
  save_job_bookmark(username, job)
  return {"message": "Job saved"}


@router.get("/saved")
async def list_saved(username: Annotated[str, Depends(get_current_username)]):
  return get_saved_jobs(username)


@router.post("/tailor-resume/{job_index}")
async def tailor_resume_endpoint(
  job_index: int,
  username: Annotated[str, Depends(get_current_username)],
):
  from app.services.resume_service import generate_pdf, tailor_resume

  jobs = get_evaluated_jobs(username)
  if job_index >= len(jobs):
    raise HTTPException(status_code=404, detail="Job not found")

  job = dict(jobs[job_index])
  profile = get_full_profile(username)
  profile["username"] = username
  result = await tailor_resume(job, username, profile)
  pdf_bytes = generate_pdf(result, username.title())

  return {
    "pdf_base64": base64.b64encode(pdf_bytes).decode(),
    "latex_code": result["latex_code"],
    "ats_score": result["ats_score"],
    "template_used": result["template_used"],
    "improvements": result["improvements"],
    "missing_keywords": result["missing_keywords"],
    "job_title": job.get("title", ""),
    "job_company": job.get("company", ""),
    "apply_url": job.get("url", ""),
  }
