"""
Base scraper utilities.
Strategy A: JSON-LD extraction bypasses fragile CSS selectors entirely.
When a page contains <script type="application/ld+json"> with
@type: JobPosting, we extract structured data directly —
immune to any frontend HTML changes.
"""

import hashlib
import json
import logging
from typing import Dict, List, Optional

from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


def make_job_id(url: str, title: str, company: str) -> str:
  """
  Strategy D: MD5 content hash as immutable job identity.
  Same job always gets same ID regardless of when scraped.
  Prevents ChromaDB/SQLite overwrite bugs.
  """
  raw = f"{url.strip()}_{title.strip().lower()}_{company.strip().lower()}"
  return hashlib.md5(raw.encode("utf-8")).hexdigest()


def extract_json_ld_jobs(html: str, source_url: str = "") -> List[Dict]:
  """
  Strategy A: Extract JobPosting schema from JSON-LD tags.
  Completely immune to HTML/CSS structure changes.
  Works on LinkedIn, Indeed, Glassdoor, company career pages.
  """
  jobs = []
  try:
    soup = BeautifulSoup(html, "lxml")
    scripts = soup.find_all("script", type="application/ld+json")

    for script in scripts:
      try:
        data = json.loads(script.string or "")
      except (json.JSONDecodeError, TypeError):
        continue

      # Handle both single object and array
      items = data if isinstance(data, list) else [data]

      for item in items:
        # Handle @graph wrapper
        if item.get("@type") == "WebPage" and "@graph" in item:
          items.extend(item["@graph"])
          continue

        if item.get("@type") != "JobPosting":
          continue

        # Extract all standard JobPosting fields
        title = item.get("title", "") or item.get("name", "")
        if not title:
          continue

        # Company extraction
        hiring_org = item.get("hiringOrganization", {})
        if isinstance(hiring_org, dict):
          company = hiring_org.get("name", "Unknown")
        else:
          company = str(hiring_org) if hiring_org else "Unknown"

        # Location extraction
        location_data = item.get("jobLocation", {})
        if isinstance(location_data, list):
          location_data = location_data[0] if location_data else {}
        if isinstance(location_data, dict):
          addr = location_data.get("address", {})
          if isinstance(addr, dict):
            location = (
              addr.get("addressLocality", "")
              or addr.get("addressRegion", "")
              or addr.get("addressCountry", "")
              or "Remote"
            )
          else:
            location = str(addr) if addr else "Remote"
        else:
          location = str(location_data) if location_data else "Remote"

        # URL
        url = item.get("url", "") or item.get("sameAs", "") or source_url

        # Description
        description = item.get("description", "")
        if description:
          # Strip HTML from description
          desc_soup = BeautifulSoup(description, "lxml")
          description = desc_soup.get_text(" ", strip=True)[:600]

        # Salary
        salary_data = item.get("baseSalary", {})
        salary = ""
        if isinstance(salary_data, dict):
          value = salary_data.get("value", {})
          if isinstance(value, dict):
            salary = (
              f"{value.get('minValue', '')}"
              f"-{value.get('maxValue', '')} "
              f"{salary_data.get('currency', '')}"
            ).strip("- ")

        # Job type
        employment_type = item.get("employmentType", "FULL_TIME")
        if isinstance(employment_type, list):
          employment_type = employment_type[0]
        job_type_map = {
          "FULL_TIME": "full-time",
          "PART_TIME": "part-time",
          "CONTRACTOR": "contract",
          "TEMPORARY": "contract",
          "INTERN": "internship",
        }
        job_type = job_type_map.get(str(employment_type).upper(), "full-time")

        job = {
          "title": title.strip(),
          "company": company.strip(),
          "location": location.strip(),
          "url": url,
          "description": description,
          "salary": salary,
          "posted_date": item.get("datePosted", "") or "Recently",
          "source": _extract_domain(source_url),
          "job_type": job_type,
          "job_id": make_job_id(url, title, company),
          "extraction_method": "json_ld",
        }
        jobs.append(job)

  except Exception as e:
    logger.warning("JSON-LD extraction error: %s", e)

  return jobs


async def fetch_with_fallback(url: str, headers: dict = None) -> Optional[str]:
  """
  Async HTTP fetch with sensible defaults.
  Uses asyncio.to_thread to avoid blocking the event loop.
  Strategy B: Non-blocking execution.
  """
  import httpx

  default_headers = {
    "User-Agent": (
      "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
      "AppleWebKit/537.36 (KHTML, like Gecko) "
      "Chrome/121.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate",
    "Connection": "keep-alive",
  }
  if headers:
    default_headers.update(headers)

  try:
    async with httpx.AsyncClient(
      timeout=15,
      follow_redirects=True,
      headers=default_headers,
    ) as client:
      r = await client.get(url)
      if r.status_code == 200:
        return r.text
  except Exception as e:
    logger.debug("Fetch failed for %s: %s", url[:50], e)
  return None


def _extract_domain(url: str) -> str:
  return (
    url.replace("https://", "")
    .replace("http://", "")
    .replace("www.", "")
    .split("/")[0]
  )
