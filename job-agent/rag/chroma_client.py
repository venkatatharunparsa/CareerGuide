import logging
from functools import lru_cache
from pathlib import Path
from typing import Any

import chromadb
from chromadb.config import Settings as ChromaSettings

from app.config import settings
logger = logging.getLogger(__name__)

_COLLECTION_NAMES = ("user_profiles", "job_listings", "career_urls")


class ChromaDBClient:
  """Persistent ChromaDB client with cosine similarity helpers."""

  def __init__(self, persist_path: str | None = None) -> None:
    path = Path(persist_path or settings.chroma_persist_path)
    path.mkdir(parents=True, exist_ok=True)
    self._client = chromadb.PersistentClient(
      path=str(path),
      settings=ChromaSettings(anonymized_telemetry=False),
    )
    self._collections: dict[str, chromadb.Collection] = {}
    logger.info("ChromaDB initialized at %s", path)

  def get_or_create_collection(self, name: str) -> chromadb.Collection:
    if name not in self._collections:
      self._collections[name] = self._client.get_or_create_collection(
        name=name,
        metadata={"hnsw:space": "cosine"},
      )
    return self._collections[name]

  def ensure_all_collections(self) -> None:
    for name in _COLLECTION_NAMES:
      self.get_or_create_collection(name)

  def add_document(
    self,
    collection_name: str,
    doc_id: str,
    text: str,
    metadata: dict[str, Any] | None = None,
  ) -> None:
    collection = self.get_or_create_collection(collection_name)
    collection.add(
      ids=[doc_id],
      documents=[text],
      metadatas=[metadata or {}],
    )

  def query_similar(
    self,
    collection_name: str,
    query_text: str,
    *,
    n_results: int = 5,
    where: dict[str, Any] | None = None,
  ) -> list[dict[str, Any]]:
    collection = self.get_or_create_collection(collection_name)
    result = collection.query(
      query_texts=[query_text],
      n_results=n_results,
      where=where,
    )
    output: list[dict[str, Any]] = []
    ids = result.get("ids", [[]])[0]
    docs = result.get("documents", [[]])[0]
    metas = result.get("metadatas", [[]])[0]
    distances = result.get("distances", [[]])[0]
    for i, doc_id in enumerate(ids):
      output.append(
        {
          "id": doc_id,
          "document": docs[i] if i < len(docs) else None,
          "metadata": metas[i] if i < len(metas) else {},
          "distance": distances[i] if i < len(distances) else None,
        }
      )
    return output

  def update_document(
    self,
    collection_name: str,
    doc_id: str,
    text: str,
    metadata: dict[str, Any] | None = None,
  ) -> None:
    collection = self.get_or_create_collection(collection_name)
    collection.update(
      ids=[doc_id],
      documents=[text],
      metadatas=[metadata or {}],
    )

  def delete_document(self, collection_name: str, doc_id: str) -> None:
    collection = self.get_or_create_collection(collection_name)
    collection.delete(ids=[doc_id])


_client: ChromaDBClient | None = None


def get_chroma_client() -> ChromaDBClient:
  global _client
  if _client is None:
    _client = ChromaDBClient()
  return _client
