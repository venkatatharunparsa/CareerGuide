import urllib.parse
from typing import Dict, List

import httpx
from bs4 import BeautifulSoup


async def scrape_wellfound(query: str, limit: int = 10) -> List[Dict]:
  """Wellfound (AngelList) — startup jobs."""
  jobs = []
  try:
    q = urllib.parse.quote(query)
    url = f"https://wellfound.com/jobs?q={q}"
    headers = {
      "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "Chrome/120.0.0.0 Safari/537.36"
      ),
    }
    async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
      r = await client.get(url, headers=headers)
    if r.status_code != 200:
      return []
    soup = BeautifulSoup(r.text, "lxml")
    cards = soup.select("div[class*='JobListing']") or soup.select("div[class*='job-listing']")
    for card in cards[:limit]:
      try:
        title_el = card.select_one("a[class*='jobTitle']") or card.select_one("h2")
        company_el = card.select_one("a[class*='companyName']") or card.select_one(
          "span[class*='company']"
        )
        location_el = card.select_one("span[class*='location']")
        if not title_el:
          continue
        href = title_el.get("href", "")
        full_url = f"https://wellfound.com{href}" if href.startswith("/") else href
        jobs.append(
          {
            "title": title_el.get_text(strip=True),
            "company": company_el.get_text(strip=True) if company_el else "Unknown",
            "location": location_el.get_text(strip=True) if location_el else "Remote",
            "url": full_url,
            "description": "",
            "posted_date": "Recently",
            "source": "wellfound.com",
            "job_type": "full-time",
          }
        )
      except Exception:
        continue
  except Exception as e:
    print(f"Wellfound scraper error: {e}")
  return jobs
