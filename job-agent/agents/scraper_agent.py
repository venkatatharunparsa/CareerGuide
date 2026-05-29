import asyncio
import logging

from agents.state import AgentState
from scraper.base_scraper import make_job_id

logger = logging.getLogger(__name__)


def cache_jobs_sync(user_id: str, jobs: list):
  """Synchronous SQLite write — called via asyncio.to_thread."""
  try:
    from app.database import cache_jobs

    cache_jobs(user_id, jobs)
  except Exception as e:
    logger.warning("cache_jobs_sync failed: %s", e)

MOCK_JOBS = [
  {
    "title": "Backend Python Developer",
    "company": "TechCorp India",
    "location": "Hyderabad, India",
    "url": "https://www.naukri.com/job-listings-123456",
    "description": "FastAPI, Python, PostgreSQL, Docker required.",
    "posted_date": "2 days ago",
    "source": "naukri.com",
    "job_type": "full-time",
  },
  {
    "title": "ML Engineer",
    "company": "AI Startup Bangalore",
    "location": "Bangalore, India",
    "url": "https://wellfound.com/jobs/123",
    "description": "LLM fine-tuning, RAG, Python, PyTorch, LangChain.",
    "posted_date": "1 day ago",
    "source": "wellfound.com",
    "job_type": "full-time",
  },
  {
    "title": "Full Stack Developer",
    "company": "Product Studio",
    "location": "Remote",
    "url": "https://remoteok.com/jobs/456",
    "description": "React, Node.js, Python, AWS, Docker.",
    "posted_date": "Today",
    "source": "remoteok.com",
    "job_type": "remote",
  },
  {
    "title": "Python Developer Internship",
    "company": "GrowthLab",
    "location": "Hyderabad, India",
    "url": "https://internshala.com/internship/789",
    "description": "Django REST APIs, data pipelines, automation.",
    "posted_date": "Today",
    "source": "internshala.com",
    "job_type": "internship",
  },
  {
    "title": "DevOps Engineer",
    "company": "CloudTech",
    "location": "Remote",
    "url": "https://himalayas.app/jobs/101",
    "description": "Docker, Kubernetes, AWS, CI/CD, Terraform.",
    "posted_date": "3 days ago",
    "source": "himalayas.app",
    "job_type": "remote",
  },
]


async def scraper_node(state: AgentState) -> AgentState:
  logger.info("Scraper starting for user %s", state["user_id"])
  instructions = state.get("scrape_instructions", {})
  keywords = state.get("search_keywords", [])
  profile = state.get("user_profile", {})
  roles = state.get("target_roles", [])

  real_jobs = await _scrape_all_sources(instructions, keywords, roles, profile)

  if real_jobs:
    logger.info("Real scrape: %d total jobs", len(real_jobs))
    jobs = real_jobs
  else:
    logger.warning("All scrapers returned 0 — using mock jobs")
    jobs = MOCK_JOBS

  # Hash-based deduplication (Strategy D)
  seen = set()
  unique = []
  for j in jobs:
    job_id = j.get("job_id") or make_job_id(
      j.get("url", ""),
      j.get("title", ""),
      j.get("company", ""),
    )
    j["job_id"] = job_id
    if job_id not in seen:
      seen.add(job_id)
      unique.append(j)

  # Non-blocking SQLite write (Strategy B)
  try:
    await asyncio.to_thread(cache_jobs_sync, state["user_id"], unique)
  except Exception as e:
    logger.warning("Cache write failed: %s", e)

  logger.info("Final unique jobs: %d", len(unique))
  return {**state, "scraped_jobs": unique, "status": "scraped"}


async def _scrape_all_sources(instructions, keywords, roles, profile) -> list:
  """Run all scrapers in parallel for maximum coverage."""
  try:
    from scraper.adzuna_scraper import scrape_arbeitnow
    from scraper.company_career_scraper import scrape_company_careers
    from scraper.github_jobs_scraper import scrape_himalayas
    from scraper.google_jobs_scraper import scrape_google_jobs
    from scraper.india_jobs_scraper import scrape_cutshort, scrape_foundit, scrape_unstop
    from scraper.internshala_scraper import scrape_internshala
    from scraper.linkedin_rss_scraper import scrape_linkedin
    from scraper.naukri_scraper import scrape_naukri
    from scraper.remoteok_scraper import scrape_remoteok
    from scraper.tavily_job_scraper import search_jobs_tavily
    from scraper.wellfound_scraper import scrape_wellfound
  except ImportError as e:
    logger.error("Import failed: %s", e)
    return []

  skills = profile.get("all_skills", profile.get("skills", []))
  main_role = roles[0] if roles else "software developer"
  main_query = keywords[0] if keywords else main_role + " " + " ".join(skills[:2])

  named_tasks = []

  for site_url, config in instructions.items():
    query = config.get("query", main_query)
    scrape_type = config.get("type", "board")

    if scrape_type == "tavily":
      named_tasks.append(
        ("tavily", search_jobs_tavily(query, roles, skills, keywords, max_results=30))
      )
    elif scrape_type == "company_career":
      named_tasks.append((f"career:{site_url[:30]}", scrape_company_careers(site_url, query, limit=8)))
    elif "naukri" in site_url:
      named_tasks.append(("naukri", scrape_naukri(query, limit=10)))
    elif "internshala" in site_url:
      named_tasks.append(("internshala", scrape_internshala(query, limit=10)))
    elif "linkedin" in site_url:
      named_tasks.append(("linkedin", scrape_linkedin(query, limit=10)))
    elif "wellfound" in site_url or "angel" in site_url:
      named_tasks.append(("wellfound", scrape_wellfound(query, limit=10)))

  named_tasks.extend(
    [
      ("remoteok_1", scrape_remoteok(main_query, limit=10)),
      ("remoteok_2", scrape_remoteok(main_role, limit=10)),
      ("himalayas_1", scrape_himalayas(main_query, limit=10)),
      ("himalayas_2", scrape_himalayas(main_role, limit=10)),
      ("arbeitnow_1", scrape_arbeitnow(main_query, limit=10)),
      ("arbeitnow_2", scrape_arbeitnow(main_role, limit=10)),
      ("foundit", scrape_foundit(main_query, limit=10)),
      ("unstop", scrape_unstop(main_query, limit=10)),
      ("cutshort", scrape_cutshort(main_query, limit=10)),
      ("google_jobs_1", scrape_google_jobs(main_query, limit=15)),
      ("google_jobs_2", scrape_google_jobs(main_role, limit=15)),
    ]
  )

  for role in roles[1:3]:
    named_tasks.extend(
      [
        (f"remoteok_{role[:10]}", scrape_remoteok(role, limit=5)),
        (f"himalayas_{role[:10]}", scrape_himalayas(role, limit=5)),
      ]
    )

  names, coros = zip(*named_tasks) if named_tasks else ([], [])
  results = await asyncio.gather(*coros, return_exceptions=True)

  all_jobs = []
  for name, result in zip(names, results):
    if isinstance(result, list) and result:
      logger.info("  %s: %d jobs", name, len(result))
      all_jobs.extend(result)
    elif isinstance(result, Exception):
      logger.warning("  %s failed: %s", name, result)
    else:
      logger.debug("  %s: 0 jobs", name)

  return all_jobs
