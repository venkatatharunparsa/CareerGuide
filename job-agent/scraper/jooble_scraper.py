from typing import Dict, List

import httpx


async def scrape_jooble(
  query: str,
  location: str = "India",
  limit: int = 10,
  api_key: str = "",
) -> List[Dict]:
  """
  Jooble API — aggregates jobs from 140+ sources.
  Get free key at: https://jooble.org/api/about
  Falls back to empty if no key.
  """
  if not api_key:
    return []
  jobs = []
  try:
    url = f"https://jooble.org/api/{api_key}"
    payload = {"keywords": query, "location": location, "page": "1"}
    headers = {"Content-Type": "application/json"}
    async with httpx.AsyncClient(timeout=30) as client:
      r = await client.post(url, json=payload, headers=headers)
    if r.status_code != 200:
      return []
    data = r.json()
    for j in data.get("jobs", [])[:limit]:
      jobs.append(
        {
          "title": j.get("title", ""),
          "company": j.get("company", "Unknown"),
          "location": j.get("location", ""),
          "url": j.get("link", ""),
          "description": j.get("snippet", ""),
          "posted_date": j.get("updated", "Recently"),
          "source": "jooble.org",
          "job_type": "full-time",
        }
      )
  except Exception as e:
    print(f"Jooble error: {e}")
  return jobs
