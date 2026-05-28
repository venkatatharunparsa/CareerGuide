import httpx
from bs4 import BeautifulSoup
from typing import Dict, List


async def scrape_internshala(query: str, limit: int = 10) -> List[Dict]:
  """Scrape Internshala for internships and jobs."""
  jobs = []
  try:
    query_encoded = query.replace(" ", "-").lower()
    url = f"https://internshala.com/internships/{query_encoded}-internship"

    headers = {
      "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
      ),
      "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }

    async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
      response = await client.get(url, headers=headers)

    if response.status_code != 200:
      return []

    soup = BeautifulSoup(response.text, "lxml")

    cards = soup.select("div.internship_meta") or soup.select("div.individual_internship")

    for card in cards[:limit]:
      try:
        title_el = card.select_one("h3.job-internship-name a") or card.select_one("a.job-title")
        company_el = card.select_one("p.company-name") or card.select_one("a.link_display_like_text")
        location_el = card.select_one("a.location_link") or card.select_one("p.location_names")
        stipend_el = card.select_one("span.stipend") or card.select_one("ins.fine")

        if not title_el:
          continue

        href = title_el.get("href", "")
        full_url = f"https://internshala.com{href}" if href.startswith("/") else href

        jobs.append(
          {
            "title": title_el.get_text(strip=True),
            "company": company_el.get_text(strip=True) if company_el else "Unknown",
            "location": location_el.get_text(strip=True) if location_el else "Remote/India",
            "url": full_url,
            "description": f"Stipend: {stipend_el.get_text(strip=True)}" if stipend_el else "",
            "posted_date": "Recently",
            "source": "internshala.com",
            "job_type": "internship",
          }
        )
      except Exception:
        continue

  except Exception as e:
    print(f"Internshala scraper error: {e}")

  return jobs
