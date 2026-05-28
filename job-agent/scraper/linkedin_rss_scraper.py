import urllib.parse
from typing import Dict, List

import httpx
from bs4 import BeautifulSoup


async def scrape_linkedin(query: str, location: str = "India", limit: int = 10) -> List[Dict]:
  """
  Scrape LinkedIn public job listings (no login required).
  Uses the public jobs search endpoint.
  """
  jobs = []
  try:
    params = urllib.parse.urlencode(
      {
        "keywords": query,
        "location": location,
        "f_TPR": "r86400",
        "sortBy": "DD",
      }
    )
    url = f"https://www.linkedin.com/jobs/search/?{params}"
    headers = {
      "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
      ),
      "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
      "Accept-Language": "en-US,en;q=0.5",
      "Accept-Encoding": "gzip, deflate, br",
      "Connection": "keep-alive",
    }
    async with httpx.AsyncClient(
      timeout=30,
      follow_redirects=True,
      headers=headers,
    ) as client:
      r = await client.get(url)

    if r.status_code != 200:
      return []

    soup = BeautifulSoup(r.text, "lxml")
    cards = soup.select("div.base-card") or soup.select("li.jobs-search__results-list > div")

    for card in cards[:limit]:
      try:
        title_el = card.select_one("h3.base-search-card__title") or card.select_one("h3")
        company_el = card.select_one("h4.base-search-card__subtitle") or card.select_one("h4")
        location_el = card.select_one("span.job-search-card__location")
        link_el = card.select_one("a.base-card__full-link") or card.select_one("a")
        time_el = card.select_one("time")

        if not title_el:
          continue

        jobs.append(
          {
            "title": title_el.get_text(strip=True),
            "company": company_el.get_text(strip=True) if company_el else "Unknown",
            "location": location_el.get_text(strip=True) if location_el else location,
            "url": link_el.get("href", "") if link_el else url,
            "description": "",
            "posted_date": time_el.get("datetime", "Recently") if time_el else "Recently",
            "source": "linkedin.com",
            "job_type": "full-time",
          }
        )
      except Exception:
        continue
  except Exception as e:
    print(f"LinkedIn scraper error: {e}")
  return jobs
