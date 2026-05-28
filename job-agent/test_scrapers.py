import asyncio
import sys

sys.path.insert(0, "scraper")


async def test_all():
  from adzuna_scraper import scrape_arbeitnow
  from github_jobs_scraper import scrape_himalayas
  from linkedin_rss_scraper import scrape_linkedin
  from remoteok_scraper import scrape_remoteok
  from weworkremotely_scraper import scrape_weworkremotely

  print("Testing open API scrapers (should always work):")
  results = await asyncio.gather(
    scrape_remoteok("python developer", limit=3),
    scrape_himalayas("python developer", limit=3),
    scrape_arbeitnow("python developer", limit=3),
    return_exceptions=True,
  )
  for name, r in zip(["RemoteOK", "Himalayas", "Arbeitnow"], results):
    if isinstance(r, list) and r:
      print(f"  [OK] {name}: {len(r)} jobs — first: {r[0]['title']} @ {r[0]['company']}")
    else:
      print(f"  [FAIL] {name}: {r}")

  print("\nTesting HTML scrapers (may be blocked):")
  results2 = await asyncio.gather(
    scrape_linkedin("python developer", limit=3),
    scrape_weworkremotely("python", limit=3),
    return_exceptions=True,
  )
  for name, r in zip(["LinkedIn", "WeWorkRemotely"], results2):
    if isinstance(r, list) and r:
      print(f"  [OK] {name}: {len(r)} jobs — first: {r[0]['title']} @ {r[0]['company']}")
    else:
      print(f"  [FAIL] {name}: {r}")


asyncio.run(test_all())
