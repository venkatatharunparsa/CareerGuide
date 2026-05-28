import httpx
from bs4 import BeautifulSoup
from typing import Dict, List


async def scrape_naukri(query: str, location: str = "India", limit: int = 10) -> List[Dict]:
  """Scrape Naukri.com using their search URL."""
  jobs = []
  try:
    query_encoded = query.replace(" ", "-").lower()
    location_encoded = location.replace(" ", "-").lower()
    url = f"https://www.naukri.com/{query_encoded}-jobs-in-{location_encoded}"

    headers = {
      "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
      ),
      "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
      "Accept-Language": "en-US,en;q=0.5",
    }

    async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
      response = await client.get(url, headers=headers)

    if response.status_code != 200:
      return []

    soup = BeautifulSoup(response.text, "lxml")

    job_cards = soup.select("article.jobTuple") or soup.select("div.jobTupleHeader")

    for card in job_cards[:limit]:
      try:
        title_el = card.select_one("a.title") or card.select_one("a.jobTitle")
        company_el = card.select_one("a.subTitle") or card.select_one("span.companyName")
        location_el = card.select_one("li.location span") or card.select_one("span.locWdth")
        exp_el = card.select_one("li.experience span") or card.select_one("span.expwdth")

        if not title_el:
          continue

        jobs.append(
          {
            "title": title_el.get_text(strip=True),
            "company": company_el.get_text(strip=True) if company_el else "Unknown",
            "location": location_el.get_text(strip=True) if location_el else location,
            "url": title_el.get("href", url),
            "description": exp_el.get_text(strip=True) if exp_el else "",
            "posted_date": "Recently",
            "source": "naukri.com",
            "job_type": "full-time",
          }
        )
      except Exception:
        continue

  except Exception as e:
    print(f"Naukri scraper error: {e}")

  return jobs
