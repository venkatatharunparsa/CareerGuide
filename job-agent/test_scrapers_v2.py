import asyncio
import sys

sys.path.insert(0, "scraper")
from dotenv import load_dotenv

load_dotenv()


async def test():
  print("=== Scraper Test v2 ===\n")

  tests = []

  try:
    from remoteok_scraper import scrape_remoteok

    tests.append(("RemoteOK", scrape_remoteok("python developer", limit=3)))
  except ImportError as e:
    print(f"RemoteOK import error: {e}")

  try:
    from github_jobs_scraper import scrape_himalayas

    tests.append(("Himalayas", scrape_himalayas("python developer", limit=3)))
  except ImportError as e:
    print(f"Himalayas import error: {e}")

  try:
    from adzuna_scraper import scrape_arbeitnow

    tests.append(("Arbeitnow", scrape_arbeitnow("python developer", limit=3)))
  except ImportError as e:
    print(f"Arbeitnow import error: {e}")

  try:
    from tavily_job_scraper import search_jobs_tavily

    tests.append(
      (
        "Tavily",
        search_jobs_tavily(
          "python developer",
          ["Backend Developer", "ML Engineer"],
          ["Python", "FastAPI", "Docker"],
          max_results=10,
        ),
      )
    )
  except ImportError as e:
    print(f"Tavily import error: {e}")

  try:
    from google_jobs_scraper import scrape_google_jobs

    tests.append(("Google Jobs", scrape_google_jobs("python developer", limit=5)))
  except ImportError as e:
    print(f"Google Jobs import error: {e}")

  try:
    from india_jobs_scraper import scrape_cutshort, scrape_foundit, scrape_unstop

    tests.append(("Foundit", scrape_foundit("python developer", limit=3)))
    tests.append(("Unstop", scrape_unstop("python developer", limit=3)))
    tests.append(("Cutshort", scrape_cutshort("python developer", limit=3)))
  except ImportError as e:
    print(f"India scrapers import error: {e}")

  try:
    from linkedin_rss_scraper import scrape_linkedin

    tests.append(("LinkedIn", scrape_linkedin("python developer", limit=3)))
  except ImportError as e:
    print(f"LinkedIn import error: {e}")

  names = [t[0] for t in tests]
  coros = [t[1] for t in tests]
  results = await asyncio.gather(*coros, return_exceptions=True)

  total = 0
  print("Results:")
  for name, r in zip(names, results):
    if isinstance(r, list):
      total += len(r)
      status = f"[OK] {len(r)} jobs"
      if r:
        status += f" — first: {r[0].get('title', '?')[:50]}"
    else:
      status = f"[FAIL] {str(r)[:80]}"
    print(f"  {name:<20} {status}")

  print(f"\nTotal jobs found: {total}")
  print("=== Done ===")


asyncio.run(test())
