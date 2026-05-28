import itertools
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class GeminiKeyRotator:
  def __init__(self, api_keys: list[str]):
    if not api_keys:
      logger.warning(
        "GeminiKeyRotator initialized with NO keys. "
        "Agent LLM calls will use mock mode."
      )
    self._keys = api_keys
    self._cycle = itertools.cycle(api_keys) if api_keys else iter([])
    self._current_index = 0
    self._total = len(api_keys)

  def get_next_key(self) -> Optional[str]:
    if not self._keys:
      return None
    key = next(self._cycle)
    self._current_index = (self._current_index + 1) % self._total
    logger.info("Using Gemini key index %d/%d", self._current_index, self._total)
    return key

  def get_all_keys(self) -> list[str]:
    return self._keys

  def has_keys(self) -> bool:
    return bool(self._keys)

  async def get_key_with_fallback(self) -> Optional[str]:
    """
    Returns a key, rotating through all available ones.
    Call this before each LLM request. On 429, call again to rotate.
    """
    return self.get_next_key()


_rotator_instance: Optional[GeminiKeyRotator] = None


def reset_key_rotator() -> None:
  global _rotator_instance
  _rotator_instance = None


def get_key_rotator() -> GeminiKeyRotator:
  global _rotator_instance
  if _rotator_instance is None:
    from app.config import get_settings

    settings = get_settings()
    keys = settings.get_gemini_keys()
    logger.info("GeminiKeyRotator loading %d key(s)", len(keys))
    _rotator_instance = GeminiKeyRotator(keys)
  return _rotator_instance
