import urllib.parse
from typing import Dict, List

import httpx


async def scrape_himalayas(query: str, limit: int = 10) -> List[Dict]:
  """
  Himalayas.app — remote jobs API, no auth needed.
  """
  jobs = []
  try:
    params = urllib.parse.urlencode({"q": query, "limit": limit})
    url = f"https://himalayas.app/jobs/api?{params}"
    headers = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}
    async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
      r = await client.get(url, headers=headers)
    if r.status_code != 200:
      return []
    data = r.json()
    job_list = data.get("jobs", [])
    for j in job_list[:limit]:
      company = j.get("company", {})
      company_name = company.get("name", "Unknown") if isinstance(company, dict) else str(company)
      jobs.append(
        {
          "title": j.get("title", ""),
          "company": company_name,
          "location": j.get("location", "Remote"),
          "url": j.get("applicationLink", j.get("url", "")),
          "description": (j.get("description", "") or "")[:500],
          "posted_date": j.get("createdAt", "Recently"),
          "source": "himalayas.app",
          "job_type": "remote",
        }
      )
  except Exception as e:
    print(f"Himalayas error: {e}")
  return jobs
