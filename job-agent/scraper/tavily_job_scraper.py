import logging
import os
from typing import Dict, List

logger = logging.getLogger(__name__)


async def search_jobs_tavily(
  query: str,
  roles: list,
  skills: list,
  max_results: int = 20,
) -> List[Dict]:
  """
  Use Tavily to search for real live job postings across the internet.
  Tavily is built for AI agents and returns clean, structured results.
  """
  api_key = os.getenv("TAVILY_API_KEY", "") or ""
  if not api_key:
    try:
      from app.config import get_settings

      api_key = get_settings().tavily_api_key or os.getenv("TAVILY_API_KEY", "") or ""
    except ImportError:
      pass
  if not api_key or "your_tavily" in api_key.lower():
    logger.warning("No TAVILY_API_KEY — skipping Tavily search")
    return []

  try:
    from tavily import TavilyClient

    client = TavilyClient(api_key=api_key)

    search_queries = [
      f"{query} jobs 2024 site:linkedin.com OR site:naukri.com OR site:indeed.com",
      f"{query} hiring now careers apply",
      f"{' '.join(skills[:3])} developer jobs remote India",
    ]

    all_jobs = []
    seen_urls = set()

    for search_query in search_queries:
      try:
        results = client.search(
          query=search_query,
          search_depth="basic",
          max_results=7,
          include_answer=False,
        )
        for r in results.get("results", []):
          url = r.get("url", "")
          title = r.get("title", "")
          content = r.get("content", "")

          if url in seen_urls:
            continue
          if not _is_job_posting(url, title, content):
            continue

          seen_urls.add(url)
          company = _extract_company(url, title)
          all_jobs.append(
            {
              "title": _clean_job_title(title),
              "company": company,
              "location": _extract_location(content),
              "url": url,
              "description": content[:600],
              "posted_date": "Recently",
              "source": _extract_domain(url),
              "job_type": "remote" if "remote" in content.lower() else "full-time",
            }
          )
      except Exception as e:
        logger.warning("Tavily query failed: %s", e)
        continue

    logger.info("Tavily found %d job postings", len(all_jobs))
    return all_jobs[:max_results]

  except Exception as e:
    logger.error("Tavily scraper error: %s", e)
    return []


def _is_job_posting(url: str, title: str, content: str) -> bool:
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
  ]
  text = (url + title + content).lower()
  return sum(1 for s in job_signals if s in text) >= 2


def _extract_company(url: str, title: str) -> str:
  domain = _extract_domain(url)
  known = {
    "linkedin.com": "via LinkedIn",
    "naukri.com": "via Naukri",
    "indeed.com": "via Indeed",
    "internshala.com": "via Internshala",
    "glassdoor.com": "via Glassdoor",
    "wellfound.com": "via Wellfound",
  }
  for k, v in known.items():
    if k in domain:
      parts = title.split(" at ")
      if len(parts) > 1:
        return parts[-1].strip()
      return v
  return domain.replace("www.", "").split(".")[0].title()


def _clean_job_title(title: str) -> str:
  for sep in [" - ", " | ", " at ", " — "]:
    if sep in title:
      return title.split(sep)[0].strip()
  return title[:80].strip()


def _extract_location(content: str) -> str:
  location_hints = [
    "remote",
    "india",
    "hyderabad",
    "bangalore",
    "mumbai",
    "delhi",
    "pune",
    "chennai",
    "united states",
    "uk",
    "germany",
  ]
  content_lower = content.lower()
  for loc in location_hints:
    if loc in content_lower:
      return loc.title()
  return "Check listing"


def _extract_domain(url: str) -> str:
  return url.replace("https://", "").replace("http://", "").replace("www.", "").split("/")[0]
