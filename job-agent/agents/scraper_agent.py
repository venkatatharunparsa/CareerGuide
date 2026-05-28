import asyncio
import logging

from agents.state import AgentState

logger = logging.getLogger(__name__)

MOCK_JOBS = [
  {
    "title": "Backend Python Developer",
    "company": "TechCorp India",
    "location": "Hyderabad, India",
    "url": "https://www.naukri.com/job-listings-123456",
    "description": "Build scalable APIs with FastAPI and Python. PostgreSQL and Docker required.",
    "posted_date": "2 days ago",
    "source": "naukri.com",
    "job_type": "full-time",
  },
  {
    "title": "ML Engineer",
    "company": "AI Startup",
    "location": "Bangalore, India (Remote)",
    "url": "https://www.naukri.com/job-listings-987654",
    "description": "LLM fine-tuning, RAG pipelines, Python, PyTorch, LangChain.",
    "posted_date": "1 day ago",
    "source": "naukri.com",
    "job_type": "full-time",
  },
  {
    "title": "Python Developer Internship",
    "company": "GrowthLab",
    "location": "Hyderabad, India",
    "url": "https://internshala.com/internship/detail/333444",
    "description": "6-month internship. Django REST APIs, data pipelines, automation.",
    "posted_date": "Today",
    "source": "internshala.com",
    "job_type": "internship",
  },
]


async def _try_real_scrape(instructions: dict) -> list:
  try:
    from scraper.adzuna_scraper import scrape_arbeitnow
    from scraper.company_career_scraper import scrape_company_careers
    from scraper.github_jobs_scraper import scrape_himalayas
    from scraper.internshala_scraper import scrape_internshala
    from scraper.linkedin_rss_scraper import scrape_linkedin
    from scraper.naukri_scraper import scrape_naukri
    from scraper.remoteok_scraper import scrape_remoteok
    from scraper.tavily_job_scraper import search_jobs_tavily
    from scraper.wellfound_scraper import scrape_wellfound
    from scraper.weworkremotely_scraper import scrape_weworkremotely
  except ImportError as e:
    logger.warning("Import failed: %s", e)
    return []

  tasks = []
  for site_url, config in instructions.items():
    query = config.get("query", "software developer")
    scrape_type = config.get("type", "board")

    if "naukri" in site_url:
      tasks.append(("naukri", scrape_naukri(query, limit=8)))
    elif "internshala" in site_url:
      tasks.append(("internshala", scrape_internshala(query, limit=8)))
    elif "linkedin" in site_url:
      tasks.append(("linkedin", scrape_linkedin(query, limit=8)))
    elif "remoteok" in site_url:
      tasks.append(("remoteok", scrape_remoteok(query, limit=8)))
    elif "wellfound" in site_url:
      tasks.append(("wellfound", scrape_wellfound(query, limit=8)))
    elif "weworkremotely" in site_url:
      tasks.append(("weworkremotely", scrape_weworkremotely(query, limit=8)))
    elif "himalayas" in site_url:
      tasks.append(("himalayas", scrape_himalayas(query, limit=8)))
    elif scrape_type == "tavily" or "tavily" in site_url:
      roles = config.get("roles", [])
      skills = config.get("skills", [])
      tasks.append(
        ("tavily", search_jobs_tavily(query, roles, skills, max_results=15))
      )
    elif scrape_type == "company_career":
      tasks.append((site_url, scrape_company_careers(site_url, query, limit=5)))
    else:
      tasks.append(("himalayas_fallback", scrape_himalayas(query, limit=5)))
      tasks.append(("arbeitnow_fallback", scrape_arbeitnow(query, limit=5)))

  all_queries = list(
    {c.get("query", "software developer") for c in instructions.values()}
  )
  main_query = all_queries[0] if all_queries else "software developer"
  tasks.append(("remoteok_always", scrape_remoteok(main_query, limit=5)))
  tasks.append(("himalayas_always", scrape_himalayas(main_query, limit=5)))
  tasks.append(("arbeitnow_always", scrape_arbeitnow(main_query, limit=5)))

  if not tasks:
    return []

  names, coros = zip(*tasks)
  results = await asyncio.gather(*coros, return_exceptions=True)

  all_jobs = []
  for name, r in zip(names, results):
    if isinstance(r, list):
      logger.info("  %s: %d jobs", name, len(r))
      all_jobs.extend(r)
    else:
      logger.warning("  %s failed: %s", name, r)

  return all_jobs


async def scraper_node(state: AgentState) -> AgentState:
  logger.info("Scraper agent starting for user %s", state["user_id"])
  instructions = state.get("scrape_instructions", {})

  real_jobs = await _try_real_scrape(instructions)

  if real_jobs:
    logger.info("Real scrape succeeded: %d jobs", len(real_jobs))
    jobs = real_jobs
  else:
    logger.info("Using mock jobs as fallback")
    jobs = MOCK_JOBS

  seen = set()
  unique = []
  for j in jobs:
    if j["url"] not in seen:
      seen.add(j["url"])
      unique.append(j)

  return {**state, "scraped_jobs": unique, "status": "scraped"}
