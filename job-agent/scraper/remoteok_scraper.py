from typing import Dict, List

import httpx
from bs4 import BeautifulSoup


async def scrape_remoteok(query: str, limit: int = 10) -> List[Dict]:
  jobs = []
  try:
    url = "https://remoteok.com/api"
    headers = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}
    async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
      r = await client.get(url, headers=headers)
    if r.status_code != 200:
      return []
    data = r.json()
    job_list = [j for j in data if isinstance(j, dict) and j.get("position")]
    query_words = query.lower().split()
    matched = []
    for j in job_list:
      text = (
        j.get("position", "")
        + " "
        + " ".join(j.get("tags", []))
        + " "
        + j.get("description", "")
      ).lower()
      if any(w in text for w in query_words):
        matched.append(j)
    source = matched if matched else job_list
    for j in source[:limit]:
      desc_html = j.get("description", "")[:500]
      jobs.append(
        {
          "title": j.get("position", ""),
          "company": j.get("company", "Unknown"),
          "location": "Remote",
          "url": j.get("url", f"https://remoteok.com/remote-jobs/{j.get('id', '')}"),
          "description": BeautifulSoup(desc_html, "lxml").get_text(),
          "posted_date": j.get("date", "Recently"),
          "source": "remoteok.com",
          "job_type": "remote",
        }
      )
  except Exception as e:
    print(f"RemoteOK error: {e}")
  return jobs
