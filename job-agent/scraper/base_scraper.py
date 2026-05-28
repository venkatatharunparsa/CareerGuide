from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ScrapeResult:
  jobs: list[dict[str, Any]] = field(default_factory=list)
  errors: list[str] = field(default_factory=list)


class BaseScraper(ABC):
  """Abstract base for site-specific job scrapers."""

  def __init__(self, site_url: str) -> None:
    self.site_url = site_url

  @abstractmethod
  async def scrape(
    self,
    query: str,
    *,
    filters: dict[str, Any] | None = None,
    seniority: str | None = None,
    limit: int = 25,
  ) -> ScrapeResult:
    """Scrape job listings for the given query."""

  def _normalize_job(self, raw: dict[str, Any], source: str) -> dict[str, Any]:
    return {
      "title": raw.get("title", "").strip(),
      "company": raw.get("company", "").strip(),
      "location": raw.get("location"),
      "url": raw.get("url", ""),
      "description": raw.get("description"),
      "posted_date": raw.get("posted_date"),
      "source": source,
    }
