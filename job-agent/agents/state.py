from typing import Optional, TypedDict


class AgentState(TypedDict, total=False):
  user_id: str
  user_profile: dict
  target_roles: list[str]
  target_urls: list[str]
  search_keywords: list[str]
  scraped_jobs: list[dict]
  filtered_jobs: list[dict]
  scrape_instructions: dict
  monitoring_updates: list[str]
  error: Optional[str]
  status: str
