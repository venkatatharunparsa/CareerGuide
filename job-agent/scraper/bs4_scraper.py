import logging
from typing import Any

import httpx
from bs4 import BeautifulSoup

from scraper.base_scraper import BaseScraper, ScrapeResult

logger = logging.getLogger(__name__)


class BS4Scraper(BaseScraper):
  """Static HTML scraper using BeautifulSoup."""

  async def scrape(
    self,
    query: str,
    *,
    filters: dict[str, Any] | None = None,
    seniority: str | None = None,
    limit: int = 25,
  ) -> ScrapeResult:
    logger.info(
      "BS4 scrape placeholder: site=%s query=%s seniority=%s",
      self.site_url,
      query,
      seniority,
    )
    try:
      async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
        response = await client.get(self.site_url, params={"q": query})
        response.raise_for_status()
        BeautifulSoup(response.text, "lxml")
    except Exception as exc:
      logger.warning("BS4 fetch failed for %s: %s", self.site_url, exc)
      return ScrapeResult(jobs=[], errors=[str(exc)])

    return ScrapeResult(
      jobs=[],
      errors=["BS4 parser selectors not yet configured for this site"],
    )
