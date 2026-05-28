import urllib.parse
from typing import Dict, List

import httpx
from bs4 import BeautifulSoup


async def scrape_google_jobs(query: str, location: str = "India", limit: int = 15) -> List[Dict]:
  """
  Scrape Google Jobs search results.
  Google indexes jobs from ALL sites — the best aggregator.
  """
  jobs = []
  try:
    params = urllib.parse.urlencode(
      {
        "q": f"{query} jobs",
        "ibp": "htl;jobs",
        "hl": "en",
        "gl": "in",
      }
    )
    url = f"https://www.google.com/search?{params}"
    headers = {
      "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
      ),
      "Accept": "text/html,application/xhtml+xml",
      "Accept-Language": "en-US,en;q=0.9",
    }
    async with httpx.AsyncClient(timeout=20, follow_redirects=True, headers=headers) as client:
      r = await client.get(url)

    if r.status_code != 200:
      return []

    soup = BeautifulSoup(r.text, "lxml")

    job_cards = (
      soup.select("div.PwjeAc")
      or soup.select("div[class*='job']")
      or soup.select("li.iFjolb")
      or soup.select("div.gws-plugins-horizon-jobs__li-ed")
    )

    for card in job_cards[:limit]:
      try:
        title_el = (
          card.select_one("div.BjJfJf") or card.select_one("h2") or card.select_one("[class*='title']")
        )
        company_el = card.select_one("div.vNEEBe") or card.select_one("[class*='company']")
        location_el = card.select_one("div.Qk80Jf") or card.select_one("[class*='location']")
        link_el = card.select_one("a")

        if not title_el:
          continue

        href = link_el.get("href", "") if link_el else ""
        jobs.append(
          {
            "title": title_el.get_text(strip=True),
            "company": company_el.get_text(strip=True) if company_el else "Unknown",
            "location": location_el.get_text(strip=True) if location_el else location,
            "url": f"https://www.google.com{href}" if href.startswith("/") else href,
            "description": "",
            "posted_date": "Recently",
            "source": "google.com/jobs",
            "job_type": "full-time",
          }
        )
      except Exception:
        continue

  except Exception as e:
    print(f"Google Jobs error: {e}")
  return jobs
