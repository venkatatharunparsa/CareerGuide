import logging
from functools import lru_cache
from typing import Any

from rag.chroma_client import get_chroma_client
from rag.collections.career_urls import CareerUrlsCollection
from rag.collections.job_listings import JobListingsCollection
from rag.collections.user_profile import UserProfileCollection

logger = logging.getLogger(__name__)


class RAGService:
  """High-level RAG operations over ChromaDB collections."""

  def __init__(self) -> None:
    client = get_chroma_client()
    self.user_profiles = UserProfileCollection(client)
    self.job_listings = JobListingsCollection(client)
    self.career_urls = CareerUrlsCollection(client)

  def initialize_collections(self) -> None:
    self.user_profiles.ensure_collection()
    self.job_listings.ensure_collection()
    self.career_urls.ensure_collection()
    logger.info("ChromaDB collections initialized")

  async def query_jobs_for_profile(
    self,
    profile_text: str,
    *,
    n_results: int = 10,
  ) -> list[dict[str, Any]]:
    return self.job_listings.query_similar(profile_text, n_results=n_results)


@lru_cache
def get_rag_service() -> RAGService:
  return RAGService()
