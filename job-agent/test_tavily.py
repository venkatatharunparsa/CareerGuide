import asyncio
import sys

from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")
sys.path.insert(0, "scraper")

from tavily_job_scraper import search_jobs_tavily


async def test():
  jobs = await search_jobs_tavily(
    query="Python developer",
    roles=["Backend Developer", "ML Engineer"],
    skills=["Python", "FastAPI", "React"],
    max_results=10,
  )
  print(f"Tavily found: {len(jobs)} jobs")
  for j in jobs[:5]:
    print(f"  - {j['title']} @ {j['company']} | {j['source']}")


asyncio.run(test())
