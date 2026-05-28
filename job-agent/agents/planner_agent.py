import asyncio
import json
import logging
import re

from agents.state import AgentState

logger = logging.getLogger(__name__)

DEFAULT_JOB_BOARDS = [
  "https://www.naukri.com",
  "https://internshala.com",
  "https://www.indeed.com",
  "https://remoteok.com",
  "https://wellfound.com",
  "https://weworkremotely.com",
  "https://himalayas.app",
  "https://www.arbeitnow.com",
  "https://www.shine.com",
  "https://www.glassdoor.com/Job",
  "https://www.foundit.in",
  "https://angel.co/jobs",
]


async def planner_node(state: AgentState) -> AgentState:
  logger.info("Planner starting for user %s", state["user_id"])
  try:
    profile = state["user_profile"]
    roles = state.get("target_roles") or profile.get("target_roles", [])
    skills = profile.get("all_skills", profile.get("skills", []))
    experience = profile.get("experience_years", 1)
    projects = profile.get("projects", [])
    experiences = profile.get("experiences", [])
    bio = profile.get("bio", "")

    extra_urls = _load_career_urls(state["user_id"])
    all_urls = list(
      dict.fromkeys(DEFAULT_JOB_BOARDS + extra_urls + state.get("target_urls", []))
    )

    keywords = _extract_keywords(skills, roles, projects, experiences)
    logger.info("Keywords: %s", keywords[:10])

    try:
      from app.services.gemini_service import get_gemini_service

      gemini = get_gemini_service()

      project_summary = "; ".join(
        [
          f"{p.get('name', '')}: {', '.join(p.get('tech_stack', [])[:3])}"
          for p in projects[:3]
        ]
      )

      prompt = f"""You are a job search strategist.

CANDIDATE:
Skills: {', '.join(skills[:25])}
Roles: {', '.join(roles)}
Experience: {experience} years
Bio: {bio[:200]}
Projects: {project_summary}

JOB BOARDS AVAILABLE:
{json.dumps(all_urls[:15], indent=2)}

TASKS:
1. Pick 8 most relevant job boards for this candidate
2. Write specific search queries using candidate skills + roles
3. Suggest 5 company career page URLs that hire this type of candidate

Return ONLY this JSON:
{{
  "sites": [
    {{"url": "<url>", "query": "<specific query>", "seniority": "entry|mid|senior"}}
  ],
  "company_career_pages": ["<url1>", "<url2>", "<url3>", "<url4>", "<url5>"]
}}"""

      resp = await asyncio.wait_for(gemini.chat(prompt), timeout=25.0)
      clean = re.sub(r"```json|```", "", resp).strip()
      s = min(
        clean.find("{") if "{" in clean else 9999,
        clean.find("[") if "[" in clean else 9999,
      )
      e = max(clean.rfind("}"), clean.rfind("]")) + 1
      data = json.loads(clean[s:e])
      sites = data.get("sites", [])
      company_pages = data.get("company_career_pages", [])

      if company_pages:
        _store_career_urls(state["user_id"], company_pages)

    except Exception as ex:
      logger.warning("Gemini planner failed: %s, using fallback", ex)
      sites = _rule_based_plan(skills, roles, all_urls)
      company_pages = []

    instructions = {}
    for site in sites:
      url = site.get("url", "")
      if url:
        instructions[url] = {
          "query": site.get("query", " ".join(roles[:2] + keywords[:2])),
          "seniority": site.get("seniority", "mid"),
        }
    for cp in company_pages:
      instructions[cp] = {
        "query": " ".join(roles[:2]),
        "type": "company_career",
        "seniority": "mid",
      }

    instructions["tavily_search"] = {
      "query": " ".join(keywords[:5] + roles[:2]),
      "type": "tavily",
      "roles": roles,
      "skills": skills[:15],
      "keywords": keywords,
    }

    logger.info(
      "Profile: %d skills, %d roles",
      len(skills),
      len(roles),
    )
    logger.info("Instructions: %s", list(instructions.keys()))
    logger.info("Planner: %d sources, keywords: %s", len(instructions), keywords[:5])
    return {
      **state,
      "scrape_instructions": instructions,
      "search_keywords": keywords,
      "status": "planned",
      "error": None,
    }

  except Exception as e:
    logger.error("Planner failed: %s", e)
    return {**state, "error": str(e), "status": "planner_failed"}


def _extract_keywords(skills, roles, projects, experiences):
  keywords = []
  keywords.extend(skills[:8])
  for role in roles[:3]:
    keywords.extend(role.split())
  for p in projects[:3]:
    keywords.extend(p.get("tech_stack", [])[:2])
  for e in experiences[:2]:
    keywords.extend(e.get("title", "").split()[:2])
  seen = set()
  result = []
  for k in keywords:
    kl = k.lower()
    if kl not in seen and len(k) > 2:
      seen.add(kl)
      result.append(k)
  return result[:15]


def _load_career_urls(user_id):
  try:
    from rag.chroma_client import ChromaDBClient

    db = ChromaDBClient()
    results = db.query_similar("career_urls", f"career pages for {user_id}", n_results=10)
    return [
      r.get("metadata", {}).get("url", "")
      for r in results
      if r.get("metadata", {}).get("url")
    ]
  except Exception:
    return []


def _store_career_urls(user_id, urls):
  try:
    from rag.chroma_client import ChromaDBClient

    db = ChromaDBClient()
    for url in urls:
      safe = url.replace("https://", "").replace("http://", "").replace("/", "_")
      db.add_document(
        collection_name="career_urls",
        doc_id=f"career_{user_id}_{safe}",
        text=f"Career page: {url}",
        metadata={"url": url, "user_id": user_id},
      )
  except Exception as e:
    logger.warning("Career URL store failed: %s", e)


def _rule_based_plan(skills, roles, urls):
  query = " ".join(roles[:2] + skills[:3])
  seniority = "entry" if len(skills) < 4 else "mid"
  return [{"url": u, "query": query, "seniority": seniority} for u in urls[:8]]
