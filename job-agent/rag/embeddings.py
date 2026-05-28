from typing import List


class EmbeddingService:
  """
  Uses ChromaDB's built-in default embedding function.
  No sentence-transformers or torch needed.
  Switch to sentence-transformers later when scraper container is added.
  """

  def embed_text(self, text: str) -> List[float]:
    # ChromaDB handles embeddings internally
    # This method kept for API compatibility
    return []

  def embed_batch(self, texts: List[str]) -> List[List[float]]:
    return [[] for _ in texts]


_instance = None


def get_embedding_service():
  global _instance
  if _instance is None:
    _instance = EmbeddingService()
  return _instance
