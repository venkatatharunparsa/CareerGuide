import asyncio
import json
import logging
import re

from agents.state import AgentState

logger = logging.getLogger(__name__)


async def monitor_node(state: AgentState) -> AgentState:
  logger.info("Evaluator starting for user %s", state["user_id"])
  profile = state["user_profile"]
  scraped = state.get("scraped_jobs", [])

  if not scraped:
    return {
      **state,
      "filtered_jobs": [],
      "status": "complete",
      "monitoring_updates": ["No jobs scraped."],
    }

  try:
    evaluated = await asyncio.wait_for(
      _semantic_evaluate(profile, scraped), timeout=25.0
    )
  except Exception as e:
    logger.warning("Semantic eval failed: %s, keyword fallback", e)
    evaluated = _keyword_evaluate(profile, scraped)

  evaluated.sort(key=lambda x: x.get("match_score", 0), reverse=True)
  top = evaluated[:25]

  try:
    from app.database import save_evaluated_jobs

    save_evaluated_jobs(state["user_id"], top)
  except Exception as e:
    logger.warning("DB save failed: %s", e)

  try:
    from rag.chroma_client import ChromaDBClient

    db = ChromaDBClient()
    for i, job in enumerate(top):
      db.add_document(
        collection_name="job_listings",
        doc_id=f"job_{state['user_id']}_{i}",
        text=f"{job['title']} {job['company']} {job.get('description', '')}",
        metadata={
          "user_id": state["user_id"],
          "title": job["title"],
          "match_score": str(job.get("match_score", 0)),
          "url": job.get("url", ""),
        },
      )
  except Exception as e:
    logger.warning("ChromaDB store failed: %s", e)

  summary = (
    f"Evaluated {len(scraped)} jobs. "
    f"{len(top)} matched (score >=50). "
    f"Top: {top[0]['title'] if top else 'none'} "
    f"({top[0].get('match_score', 0) if top else 0}% match)."
  )

  logger.info("Monitor complete. %d jobs passed filter.", len(top))

  return {
    **state,
    "filtered_jobs": top,
    "status": "complete",
    "monitoring_updates": [summary],
  }


async def _semantic_evaluate(profile, jobs):
  from app.services.gemini_service import get_gemini_service

  gemini = get_gemini_service()

  skills = profile.get("all_skills", profile.get("skills", []))
  roles = profile.get("target_roles", [])
  bio = profile.get("bio", "")
  experience = profile.get("experience_years", 1)
  projects = profile.get("projects", [])
  experiences_list = profile.get("experiences", [])

  proj_summary = "; ".join(
    [
      f"{p.get('name', '')}: {p.get('description', '')[:80]}"
      for p in projects[:4]
    ]
  )
  exp_summary = "; ".join(
    [
      f"{e.get('title', '')} at {e.get('organization', '')}"
      for e in experiences_list[:3]
    ]
  )

  all_results = []
  batch_size = 8

  for i in range(0, min(len(jobs), 40), batch_size):
    batch = jobs[i : i + batch_size]
    jobs_json = json.dumps(
      [
        {
          "index": i + j,
          "title": job.get("title", ""),
          "company": job.get("company", ""),
          "description": job.get("description", "")[:400],
          "job_type": job.get("job_type", ""),
        }
        for j, job in enumerate(batch)
      ],
      indent=2,
    )

    prompt = f"""You are an expert technical recruiter.

CANDIDATE:
Skills: {', '.join(skills[:30])}
Target roles: {', '.join(roles)}
Experience: {experience} years
Bio: {bio[:200]}
Projects: {proj_summary}
Work history: {exp_summary}

JOBS TO EVALUATE (JSON):
{jobs_json}

Score each job 0-100 based on:
- Skill match (35%): overlap between candidate skills and job requirements
- Role alignment (25%): how well title/description matches target roles
- Experience fit (20%): seniority level match
- Project/domain relevance (20%): do candidate projects relate to this domain

For each job also provide:
- matched_skills: skills candidate has that job wants
- missing_skills: key skills job wants that candidate lacks
- skill_gaps: top 3 skills to learn for this role
- learning_suggestions: how to acquire missing skills
- reasoning: 1 sentence explaining the score

Return ONLY a JSON array:
[{{
  "index": 0,
  "score": 85,
  "matched_skills": ["Python","FastAPI"],
  "missing_skills": ["Kubernetes"],
  "skill_gaps": ["Kubernetes","Helm","ArgoCD"],
  "learning_suggestions": ["Take CKA course","Build a k8s side project"],
  "reasoning": "Strong backend match, missing cloud-native deployment skills"
}}]"""

    try:
      resp = await asyncio.wait_for(gemini.chat(prompt), timeout=12.0)
      clean = re.sub(r"```json|```", "", resp).strip()
      s = clean.find("[")
      e = clean.rfind("]") + 1
      scores = json.loads(clean[s:e])
      for item in scores:
        idx = item.get("index", 0)
        if isinstance(idx, int) and 0 <= idx < len(jobs):
          jc = dict(jobs[idx])
          jc["match_score"] = int(item.get("score", 0) or 0)
          jc["match_reason"] = item.get("reasoning", "")
          jc["matched_skills"] = item.get("matched_skills", []) or []
          jc["missing_skills"] = item.get("missing_skills", []) or []
          jc["skill_gaps"] = item.get("skill_gaps", []) or []
          jc["learning_suggestions"] = item.get("learning_suggestions", []) or []
          if jc["match_score"] >= 45:
            all_results.append(jc)
    except Exception as ex:
      logger.warning("Batch %d eval failed: %s", i, ex)
      for job in batch:
        ev = _evaluate_single(profile, job)
        if ev["match_score"] >= 45:
          all_results.append(ev)

  return all_results


def _keyword_evaluate(profile, jobs):
  return [
    j
    for j in [_evaluate_single(profile, job) for job in jobs]
    if j["match_score"] >= 45
  ]


def _evaluate_single(profile, job):
  skills = [s.lower() for s in profile.get("all_skills", profile.get("skills", []))]
  roles = [r.lower() for r in profile.get("target_roles", [])]
  projects = profile.get("projects", [])

  text = (
    job.get("title", "")
    + " "
    + job.get("description", "")
    + " "
    + job.get("company", "")
  ).lower()

  matched = [s for s in skills if s in text]
  role_hit = any(any(w in text for w in r.split()) for r in roles)

  proj_score = 0
  for p in projects[:3]:
    pt = " ".join(p.get("tech_stack", [])).lower()
    if any(t in text for t in pt.split()[:5]):
      proj_score += 8

  skill_pct = min(len(matched) / max(len(skills), 1) * 60, 60)
  role_pts = 25 if role_hit else 0
  score = min(int(skill_pct + role_pts + proj_score) + 15, 99)

  jc = dict(job)
  jc["match_score"] = score
  jc["match_reason"] = f"Matched {len(matched)} skills: {', '.join(matched[:5])}"
  jc["matched_skills"] = matched[:10]
  jc["missing_skills"] = []
  jc["skill_gaps"] = []
  jc["learning_suggestions"] = []
  return jc
