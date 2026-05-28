import urllib.parse
from typing import Dict, List

import httpx
from bs4 import BeautifulSoup


async def scrape_indeed(query: str, location: str = "India", limit: int = 10) -> List[Dict]:
  jobs = []
  try:
    params = urllib.parse.urlencode({"q": query, "l": location, "sort": "date"})
    url = f"https://www.indeed.com/jobs?{params}"
    headers = {
      "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "Chrome/120.0.0.0 Safari/537.36"
      ),
      "Accept-Language": "en-US,en;q=0.9",
    }
    async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
      r = await client.get(url, headers=headers)
    if r.status_code != 200:
      return []
    soup = BeautifulSoup(r.text, "lxml")
    cards = soup.select("div.job_seen_beacon") or soup.select("div.jobsearch-SerpJobCard")
    for card in cards[:limit]:
      try:
        title_el = card.select_one("h2.jobTitle span") or card.select_one("a.jobtitle")
        company_el = card.select_one("span.companyName") or card.select_one("span.company")
        location_el = card.select_one("div.companyLocation") or card.select_one("span.location")
        link_el = card.select_one("a[id^='job_']") or card.select_one("a.jobtitle")
        if not title_el:
          continue
        href = link_el.get("href", "") if link_el else ""
        full_url = f"https://www.indeed.com{href}" if href.startswith("/") else href
        jobs.append(
          {
            "title": title_el.get_text(strip=True),
            "company": company_el.get_text(strip=True) if company_el else "Unknown",
            "location": location_el.get_text(strip=True) if location_el else location,
            "url": full_url,
            "description": "",
            "posted_date": "Recently",
            "source": "indeed.com",
            "job_type": "full-time",
          }
        )
      except Exception:
        continue
  except Exception as e:
    print(f"Indeed scraper error: {e}")
  return jobs
