import logging
from typing import Dict, List

from bs4 import BeautifulSoup

from scraper.base_scraper import extract_json_ld_jobs, fetch_with_fallback, make_job_id

logger = logging.getLogger(__name__)


async def scrape_naukri(
  query: str,
  location: str = "India",
  limit: int = 10,
) -> List[Dict]:
  jobs = []
  try:
    query_encoded = query.replace(" ", "-").lower()
    location_encoded = location.replace(" ", "-").lower()
    url = f"https://www.naukri.com/{query_encoded}-jobs-in-{location_encoded}"

    html = await fetch_with_fallback(url)
    if not html:
      return []

    # Strategy A: Try JSON-LD first
    ld_jobs = extract_json_ld_jobs(html, url)
    if ld_jobs:
      logger.info("Naukri JSON-LD: %d jobs", len(ld_jobs))
      return ld_jobs[:limit]

    # Fallback: CSS selectors
    soup = BeautifulSoup(html, "lxml")
    selectors = [
      "article.jobTuple",
      "div.jobTupleHeader",
      "div[class*='job-tuple']",
      "div[class*='JobTuple']",
      "li[class*='job']",
    ]
    cards = []
    for sel in selectors:
      cards = soup.select(sel)
      if cards:
        break

    for card in cards[:limit]:
      try:
        title_el = (
          card.select_one("a.title")
          or card.select_one("a.jobTitle")
          or card.select_one("h2 a")
          or card.select_one("a[class*='title']")
        )
        company_el = (
          card.select_one("a.subTitle")
          or card.select_one("span.companyName")
          or card.select_one("[class*='company']")
        )
        location_el = (
          card.select_one("li.location span")
          or card.select_one("span.locWdth")
          or card.select_one("[class*='location']")
        )
        if not title_el:
          continue
        href = title_el.get("href", url)
        title = title_el.get_text(strip=True)
        company = company_el.get_text(strip=True) if company_el else "Unknown"
        jobs.append(
          {
            "title": title,
            "company": company,
            "location": location_el.get_text(strip=True) if location_el else location,
            "url": href,
            "description": "",
            "posted_date": "Recently",
            "source": "naukri.com",
            "job_type": "full-time",
            "job_id": make_job_id(href, title, company),
          }
        )
      except Exception:
        continue

  except Exception as e:
    logger.warning("Naukri scraper error: %s", e)
  return jobs
