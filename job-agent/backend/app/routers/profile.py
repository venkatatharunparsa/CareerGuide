import json
import logging
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from app.database import (
  delete_experience,
  delete_project,
  delete_resume,
  get_experiences,
  get_full_profile,
  get_projects,
  get_resumes,
  save_experience,
  save_profile,
  save_project,
  save_resume,
  set_primary_resume,
)
from app.dependencies import get_current_username

logger = logging.getLogger(__name__)
router = APIRouter()


def _parse_resume_text(file_bytes: bytes, filename: str) -> str:
  try:
    if filename.lower().endswith(".pdf"):
      import io

      import PyPDF2

      r = PyPDF2.PdfReader(io.BytesIO(file_bytes))
      return "\n".join(p.extract_text() or "" for p in r.pages)
    elif filename.lower().endswith(".docx"):
      import io

      import docx

      d = docx.Document(io.BytesIO(file_bytes))
      return "\n".join(p.text for p in d.paragraphs)
  except Exception as e:
    logger.warning("Resume parse error: %s", e)
  return ""


@router.get("/")
async def get_profile(username: Annotated[str, Depends(get_current_username)]):
  return get_full_profile(username)


@router.post("/update")
async def update_profile(
  username: Annotated[str, Depends(get_current_username)],
  skills: str = Form("[]"),
  target_roles: str = Form("[]"),
  experience_years: int = Form(1),
  bio: str = Form(""),
):
  from app.services.profile_service import build_master_skill_set

  manual_skills = json.loads(skills)
  roles = json.loads(target_roles)

  existing_projects = get_projects(username)
  existing_exps = get_experiences(username)
  resumes = get_resumes(username)
  resume_text = resumes[0]["raw_text"] if resumes else ""

  master_skills = await build_master_skill_set(
    username, manual_skills, resume_text, existing_projects, existing_exps
  )

  save_profile(username, master_skills, roles, experience_years, bio)

  try:
    from rag.chroma_client import ChromaDBClient

    db = ChromaDBClient()
    proj_text = " ".join(
      [p.get("name", "") + ": " + p.get("description", "") for p in existing_projects]
    )
    db.add_document(
      collection_name="user_profiles",
      doc_id=f"profile_{username}",
      text=(
        f"Skills: {', '.join(master_skills)}\n"
        f"Roles: {', '.join(roles)}\n"
        f"Bio: {bio}\nProjects: {proj_text}\n"
        f"Resume: {resume_text[:500]}"
      ),
      metadata={
        "username": username,
        "skills": json.dumps(master_skills),
        "roles": json.dumps(roles),
      },
    )
  except Exception as e:
    logger.warning("ChromaDB update failed: %s", e)

  return {
    "message": "profile updated",
    "total_skills": len(master_skills),
    "skills": master_skills,
  }


@router.post("/resume/upload")
async def upload_resume(
  username: Annotated[str, Depends(get_current_username)],
  file: UploadFile = File(...),
  set_as_primary: bool = Form(True),
):
  from app.services.profile_service import (
    extract_skills_from_text,
    extract_skills_with_gemini,
  )

  file_bytes = await file.read()
  raw_text = _parse_resume_text(file_bytes, file.filename or "")
  if not raw_text:
    raise HTTPException(status_code=400, detail="Could not extract text from resume")
  auto_skills = extract_skills_from_text(raw_text)
  gemini_skills = await extract_skills_with_gemini(raw_text, auto_skills)
  all_skills = list(dict.fromkeys(auto_skills + gemini_skills))
  save_resume(username, file.filename or "resume.pdf", raw_text, all_skills, set_as_primary)
  return {
    "message": "Resume uploaded",
    "filename": file.filename,
    "extracted_skills": all_skills,
    "skill_count": len(all_skills),
  }


@router.get("/resume/list")
async def list_resumes(username: Annotated[str, Depends(get_current_username)]):
  return get_resumes(username)


@router.post("/resume/{resume_id}/set-primary")
async def set_primary(
  resume_id: int,
  username: Annotated[str, Depends(get_current_username)],
):
  set_primary_resume(username, resume_id)
  return {"message": "Primary resume updated"}


@router.delete("/resume/{resume_id}")
async def remove_resume(
  resume_id: int,
  username: Annotated[str, Depends(get_current_username)],
):
  delete_resume(username, resume_id)
  return {"message": "Resume deleted"}


@router.post("/project/add")
async def add_project(
  username: Annotated[str, Depends(get_current_username)],
  name: str = Form(...),
  description: str = Form(""),
  tech_stack: str = Form("[]"),
  url: str = Form(""),
  role: str = Form(""),
  outcome: str = Form(""),
):
  from app.services.profile_service import extract_from_project

  tech = json.loads(tech_stack)
  proj = {
    "description": description,
    "tech_stack": tech,
    "role": role,
    "outcome": outcome,
  }
  auto_tech = extract_from_project(proj)
  merged_tech = list(dict.fromkeys(tech + auto_tech))
  save_project(username, name, description, merged_tech, url, role, outcome)
  return {"message": "Project added", "tech_stack": merged_tech}


@router.get("/project/list")
async def list_projects(username: Annotated[str, Depends(get_current_username)]):
  return get_projects(username)


@router.delete("/project/{project_id}")
async def remove_project(
  project_id: int,
  username: Annotated[str, Depends(get_current_username)],
):
  delete_project(username, project_id)
  return {"message": "Project deleted"}


@router.post("/experience/add")
async def add_experience(
  username: Annotated[str, Depends(get_current_username)],
  exp_type: str = Form("job"),
  title: str = Form(...),
  organization: str = Form(...),
  description: str = Form(""),
  skills_used: str = Form("[]"),
  start_date: str = Form(""),
  end_date: str = Form(""),
  is_current: bool = Form(False),
):
  from app.services.profile_service import extract_from_experience

  skills = json.loads(skills_used)
  exp = {"description": description, "title": title, "skills_used": skills}
  auto_skills = extract_from_experience(exp)
  merged = list(dict.fromkeys(skills + auto_skills))
  save_experience(
    username,
    exp_type,
    title,
    organization,
    description,
    merged,
    start_date,
    end_date,
    is_current,
  )
  return {"message": "Experience added", "skills_extracted": merged}


@router.get("/experience/list")
async def list_experiences(username: Annotated[str, Depends(get_current_username)]):
  return get_experiences(username)


@router.delete("/experience/{exp_id}")
async def remove_experience(
  exp_id: int,
  username: Annotated[str, Depends(get_current_username)],
):
  delete_experience(username, exp_id)
  return {"message": "Experience deleted"}
