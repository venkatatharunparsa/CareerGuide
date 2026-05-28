from typing import Dict, List

import httpx
from bs4 import BeautifulSoup

COMMON_CAREER_PATHS = [
  "/careers",
  "/jobs",
  "/career",
  "/work-with-us",
  "/join-us",
  "/opportunities",
  "/hiring",
]


async def scrape_company_careers(company_url: str, query: str, limit: int = 5) -> List[Dict]:
  """
  Given a company base URL, find their careers page and scrape jobs.
  Tries common career page paths automatically.
  """
  jobs = []
  headers = {
    "User-Agent": (
      "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "Chrome/120.0.0.0 Safari/537.36"
    )
  }
  base = company_url.rstrip("/")
  career_page_html = ""
  career_url = ""

  async with httpx.AsyncClient(timeout=20, follow_redirects=True) as client:
    for path in COMMON_CAREER_PATHS:
      try:
        r = await client.get(f"{base}{path}", headers=headers)
        if r.status_code == 200 and len(r.text) > 1000:
          career_page_html = r.text
          career_url = f"{base}{path}"
          break
      except Exception:
        continue

  if not career_page_html:
    return []

  try:
    soup = BeautifulSoup(career_page_html, "lxml")
    query_lower = query.lower()
    domain = base.replace("https://", "").replace("http://", "").split("/")[0]

    all_links = soup.find_all("a", href=True)
    for link in all_links[:50]:
      text = link.get_text(strip=True)
      href = link.get("href", "")
      if not text or len(text) < 5:
        continue
      if any(kw in text.lower() for kw in query_lower.split()):
        full_url = href if href.startswith("http") else f"{base}{href}"
        jobs.append(
          {
            "title": text,
            "company": domain,
            "location": "Check listing",
            "url": full_url,
            "description": f"Found on {career_url}",
            "posted_date": "Recently",
            "source": domain,
            "job_type": "full-time",
          }
        )
      if len(jobs) >= limit:
        break
  except Exception as e:
    print(f"Company career scraper error for {company_url}: {e}")

  return jobs
