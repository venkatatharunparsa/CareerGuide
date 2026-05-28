import asyncio
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")
sys.path.insert(0, "scraper")

from tavily_job_scraper import search_jobs_tavily


async def test():
  jobs = await search_jobs_tavily(
    "Python developer",
    ["Backend Developer"],
    ["Python", "FastAPI"],
    10,
  )
  print(f"Tavily: {len(jobs)} jobs")
  sources = sorted({j["source"] for j in jobs})
  print(f"Sources: {sources}")
  for j in jobs[:3]:
    print(f"  - {j['title']} @ {j['company']} | {j['source']}")


asyncio.run(test())
