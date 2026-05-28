import asyncio
import logging
import os
from typing import Dict, List

from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


async def search_jobs_tavily(
  query: str,
  roles: list,
  skills: list,
  keywords: list = None,
  max_results: int = 30,
) -> List[Dict]:
  api_key = os.getenv("TAVILY_API_KEY", "")
  if not api_key:
    return []

  try:
    from tavily import TavilyClient

    client = TavilyClient(api_key=api_key)
  except Exception as e:
    logger.error("Tavily init failed: %s", e)
    return []

  top_skills = skills[:4] if skills else []
  top_roles = roles[:2] if roles else ["software developer"]
  kw = keywords[:3] if keywords else top_skills[:3]

  search_queries = [
    f"{top_roles[0]} jobs 2025 apply now",
    f"{' '.join(top_skills[:3])} developer jobs hiring",
    f"site:linkedin.com/jobs {top_roles[0]} {top_skills[0] if top_skills else ''}",
    f"site:naukri.com {top_roles[0]} jobs",
    f"site:indeed.com {top_roles[0]} jobs",
    f"site:wellfound.com {top_roles[0]} jobs",
    f"site:internshala.com {top_roles[0]} internship",
    f"{top_roles[0]} remote job {top_skills[0] if top_skills else ''} 2025",
    f"{' '.join(kw[:2])} engineer jobs remote work from home",
    f"{top_roles[0]} {top_skills[0] if top_skills else ''} careers hiring now",
    f"{top_roles[0]} jobs India Hyderabad Bangalore 2025",
    f"{' '.join(top_skills[:2])} developer fresher jobs India",
  ]

  all_jobs = []
  seen_urls = set()

  for i in range(0, len(search_queries), 3):
    batch = search_queries[i : i + 3]
    tasks = [_tavily_search(client, q, seen_urls) for q in batch]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    for r in results:
      if isinstance(r, list):
        all_jobs.extend(r)
        seen_urls.update(j["url"] for j in r)
    if i + 3 < len(search_queries):
      await asyncio.sleep(0.5)

  logger.info("Tavily total: %d jobs from %d queries", len(all_jobs), len(search_queries))
  return all_jobs[:max_results]


async def _tavily_search(client, query: str, seen_urls: set) -> List[Dict]:
  try:
    results = client.search(
      query=query,
      search_depth="basic",
      max_results=5,
      include_answer=False,
    )
    jobs = []
    for r in results.get("results", []):
      url = r.get("url", "")
      if url in seen_urls or not url:
        continue
      title = r.get("title", "")
      content = r.get("content", "")
      if not _is_job_posting(url, title, content):
        continue
      jobs.append(
        {
          "title": _clean_title(title),
          "company": _extract_company(url, title, content),
          "location": _extract_location(content),
          "url": url,
          "description": content[:600],
          "posted_date": "Recently",
          "source": _extract_domain(url),
          "job_type": "remote" if "remote" in content.lower() else "full-time",
        }
      )
    return jobs
  except Exception as e:
    logger.warning("Tavily query '%s' failed: %s", query[:30], e)
    return []


def _is_job_posting(url, title, content):
  job_signals = [
    "job",
    "career",
    "hiring",
    "position",
    "role",
    "engineer",
    "developer",
    "analyst",
    "manager",
    "apply",
    "vacancy",
    "opening",
    "internship",
    "opportunity",
    "recruit",
    "full-time",
    "part-time",
    "remote",
    "salary",
    "experience",
  ]
  text = (url + " " + title + " " + content).lower()
  return sum(1 for s in job_signals if s in text) >= 2


def _extract_company(url, title, content):
  del content
  domain = _extract_domain(url)
  known = {
    "linkedin.com": None,
    "naukri.com": None,
    "indeed.com": None,
    "glassdoor.com": None,
    "wellfound.com": None,
    "internshala.com": None,
  }
  for k in known:
    if k in domain:
      for sep in [" at ", " - ", " | ", " @ "]:
        if sep in title:
          parts = title.split(sep)
          if len(parts) > 1:
            return parts[-1].strip()[:60]
      return f"via {domain}"
  return domain.replace("www.", "").split(".")[0].title()


def _clean_title(title):
  for sep in [" - ", " | ", " at ", " — ", " @ "]:
    if sep in title:
      return title.split(sep)[0].strip()[:100]
  return title[:100].strip()


def _extract_location(content):
  locations = [
    "remote",
    "india",
    "hyderabad",
    "bangalore",
    "bengaluru",
    "mumbai",
    "delhi",
    "pune",
    "chennai",
    "noida",
    "gurgaon",
    "united states",
    "uk",
    "germany",
    "canada",
    "australia",
    "singapore",
    "dubai",
    "worldwide",
  ]
  cl = content.lower()
  for loc in locations:
    if loc in cl:
      return loc.title()
  return "Check listing"


def _extract_domain(url):
  return url.replace("https://", "").replace("http://", "").replace("www.", "").split("/")[0]
