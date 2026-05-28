from typing import Dict, List

import httpx


async def scrape_arbeitnow(query: str, limit: int = 10) -> List[Dict]:
  """
  Arbeitnow — free public API, no key needed.
  https://www.arbeitnow.com/api/job-board-api
  """
  jobs = []
  try:
    url = "https://www.arbeitnow.com/api/job-board-api"
    headers = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}
    async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
      r = await client.get(url, headers=headers)
    if r.status_code != 200:
      return []
    data = r.json()
    job_list = data.get("data", [])
    query_words = query.lower().split()
    matched = [
      j
      for j in job_list
      if any(
        w in (j.get("title", "") + j.get("description", "")).lower() for w in query_words
      )
    ]
    source = matched if matched else job_list
    for j in source[:limit]:
      jobs.append(
        {
          "title": j.get("title", ""),
          "company": j.get("company_name", "Unknown"),
          "location": j.get("location", "Remote"),
          "url": j.get("url", ""),
          "description": (j.get("description", "") or "")[:500],
          "posted_date": j.get("created_at", "Recently"),
          "source": "arbeitnow.com",
          "job_type": "remote" if j.get("remote") else "full-time",
        }
      )
  except Exception as e:
    print(f"Arbeitnow error: {e}")
  return jobs
