from typing import Any

from rag.chroma_client import ChromaDBClient

_COLLECTION = "job_listings"


class JobListingsCollection:
  def __init__(self, client: ChromaDBClient) -> None:
    self._client = client

  def ensure_collection(self) -> None:
    self._client.get_or_create_collection(_COLLECTION)

  def add_document(
    self, doc_id: str, text: str, metadata: dict[str, Any] | None = None
  ) -> None:
    self._client.add_document(_COLLECTION, doc_id, text, metadata)

  def query_similar(self, query_text: str, *, n_results: int = 5) -> list[dict[str, Any]]:
    return self._client.query_similar(_COLLECTION, query_text, n_results=n_results)

  def update_document(
    self, doc_id: str, text: str, metadata: dict[str, Any] | None = None
  ) -> None:
    self._client.update_document(_COLLECTION, doc_id, text, metadata)

  def delete_document(self, doc_id: str) -> None:
    self._client.delete_document(_COLLECTION, doc_id)
