import urllib.parse
from typing import Dict, List

import httpx
from bs4 import BeautifulSoup


async def scrape_foundit(query: str, limit: int = 10) -> List[Dict]:
  """foundit.in (formerly Monster India)"""
  jobs = []
  try:
    q = urllib.parse.quote(query)
    url = f"https://www.foundit.in/srp/results?query={q}&experienceRanges=0~3"
    headers = {
      "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "Chrome/121.0.0.0 Safari/537.36"
      )
    }
    async with httpx.AsyncClient(timeout=20, follow_redirects=True) as client:
      r = await client.get(url, headers=headers)
    if r.status_code != 200:
      return []
    soup = BeautifulSoup(r.text, "lxml")
    cards = soup.select("div.srpResultCardContainer") or soup.select("div.jobCard") or soup.select("div[class*='card']")
    for card in cards[:limit]:
      try:
        title_el = card.select_one("h3.jobTitle") or card.select_one("a.title") or card.select_one("h2")
        company_el = card.select_one("span.companyName")
        location_el = card.select_one("span.location")
        link_el = card.select_one("a")
        if not title_el:
          continue
        href = link_el.get("href", "") if link_el else ""
        full_url = f"https://www.foundit.in{href}" if href.startswith("/") else href
        jobs.append(
          {
            "title": title_el.get_text(strip=True),
            "company": company_el.get_text(strip=True) if company_el else "Unknown",
            "location": location_el.get_text(strip=True) if location_el else "India",
            "url": full_url,
            "description": "",
            "posted_date": "Recently",
            "source": "foundit.in",
            "job_type": "full-time",
          }
        )
      except Exception:
        continue
  except Exception as e:
    print(f"Foundit error: {e}")
  return jobs


async def scrape_unstop(query: str, limit: int = 10) -> List[Dict]:
  """Unstop — competitions, hackathons, jobs for students"""
  jobs = []
  try:
    q = urllib.parse.quote(query)
    url = (
      "https://unstop.com/api/public/opportunity/search-result"
      f"?opportunity=jobs&searchTerm={q}&per_page={limit}"
    )
    headers = {
      "User-Agent": "Mozilla/5.0",
      "Accept": "application/json",
    }
    async with httpx.AsyncClient(timeout=20) as client:
      r = await client.get(url, headers=headers)
    if r.status_code != 200:
      return []
    data = r.json()
    items = data.get("data", {}).get("data", [])
    for item in items[:limit]:
      jobs.append(
        {
          "title": item.get("title", ""),
          "company": item.get("organisation", {}).get("name", "Unknown"),
          "location": item.get("city", "Remote"),
          "url": f"https://unstop.com/jobs/{item.get('public_url', '')}",
          "description": item.get("description", "")[:300],
          "posted_date": item.get("start_date", "Recently"),
          "source": "unstop.com",
          "job_type": "full-time",
        }
      )
  except Exception as e:
    print(f"Unstop error: {e}")
  return jobs


async def scrape_cutshort(query: str, limit: int = 10) -> List[Dict]:
  """Cutshort — tech jobs India"""
  jobs = []
  try:
    q = urllib.parse.quote(query)
    url = f"https://cutshort.io/jobs?q={q}"
    headers = {
      "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "Chrome/121.0.0.0 Safari/537.36"
      ),
      "Accept": "text/html",
    }
    async with httpx.AsyncClient(timeout=20, follow_redirects=True) as client:
      r = await client.get(url, headers=headers)
    if r.status_code != 200:
      return []
    soup = BeautifulSoup(r.text, "lxml")
    cards = soup.select("div.job-card") or soup.select("div[class*='JobCard']") or soup.select("li[class*='job']")
    for card in cards[:limit]:
      try:
        title_el = card.select_one("h2") or card.select_one("h3") or card.select_one("a")
        company_el = card.select_one("[class*='company']")
        link_el = card.select_one("a")
        if not title_el:
          continue
        href = link_el.get("href", "") if link_el else ""
        full_url = f"https://cutshort.io{href}" if href.startswith("/") else href
        jobs.append(
          {
            "title": title_el.get_text(strip=True),
            "company": company_el.get_text(strip=True) if company_el else "Unknown",
            "location": "India",
            "url": full_url,
            "description": "",
            "posted_date": "Recently",
            "source": "cutshort.io",
            "job_type": "full-time",
          }
        )
      except Exception:
        continue
  except Exception as e:
    print(f"Cutshort error: {e}")
  return jobs
