import urllib.parse
from typing import Dict, List

import httpx
from bs4 import BeautifulSoup


async def scrape_weworkremotely(query: str, limit: int = 10) -> List[Dict]:
  jobs = []
  try:
    q = urllib.parse.quote(query)
    url = f"https://weworkremotely.com/remote-jobs/search?term={q}"
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
    cards = soup.select("ul.jobs li") or soup.select("article")
    for card in cards[:limit]:
      try:
        title_el = card.select_one("span.title") or card.select_one("h4")
        company_el = card.select_one("span.company") or card.select_one("h3")
        link_el = card.select_one("a[href*='/remote-jobs/']")
        if not title_el or not link_el:
          continue
        href = link_el.get("href", "")
        full_url = f"https://weworkremotely.com{href}" if href.startswith("/") else href
        jobs.append(
          {
            "title": title_el.get_text(strip=True),
            "company": company_el.get_text(strip=True) if company_el else "Unknown",
            "location": "Remote",
            "url": full_url,
            "description": "",
            "posted_date": "Recently",
            "source": "weworkremotely.com",
            "job_type": "remote",
          }
        )
      except Exception:
        continue
  except Exception as e:
    print(f"WeWorkRemotely scraper error: {e}")
  return jobs
