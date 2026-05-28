import urllib.parse
from typing import Dict, List

import httpx


async def scrape_adzuna(query: str, location: str = "india", limit: int = 10) -> List[Dict]:
  """
  Adzuna aggregates jobs from 100+ sources.
  Free API: https://developer.adzuna.com
  """
  jobs = []
  try:
    params = urllib.parse.urlencode(
      {
        "q": query,
        "where": location,
        "results_per_page": limit,
        "content-type": "application/json",
      }
    )
    url = f"https://www.adzuna.in/search?{params}"
    headers = {
      "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "Chrome/121.0.0.0 Safari/537.36"
      )
    }
    from bs4 import BeautifulSoup

    async with httpx.AsyncClient(timeout=20, follow_redirects=True) as client:
      r = await client.get(url, headers=headers)

    if r.status_code != 200:
      return []

    soup = BeautifulSoup(r.text, "lxml")
    cards = soup.select("article.result") or soup.select("div[data-aid]") or soup.select("div.a-result")

    for card in cards[:limit]:
      try:
        title_el = card.select_one("h2 a") or card.select_one(".title a")
        company_el = card.select_one(".advert-company")
        location_el = card.select_one(".location")
        desc_el = card.select_one(".description")

        if not title_el:
          continue

        jobs.append(
          {
            "title": title_el.get_text(strip=True),
            "company": company_el.get_text(strip=True) if company_el else "Unknown",
            "location": location_el.get_text(strip=True) if location_el else location,
            "url": title_el.get("href", ""),
            "description": desc_el.get_text(strip=True)[:300] if desc_el else "",
            "posted_date": "Recently",
            "source": "adzuna.in",
            "job_type": "full-time",
          }
        )
      except Exception:
        continue
  except Exception as e:
    print(f"Adzuna error: {e}")
  return jobs
