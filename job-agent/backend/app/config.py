import os
from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def _discover_env_files() -> tuple[str, ...]:
  """Find .env on disk; Docker usually injects vars via compose env_file instead."""
  candidates = [
    Path(__file__).resolve().parents[2] / ".env",  # repo root (local dev)
    Path("/app/.env"),  # optional mount in container
    Path.cwd() / ".env",
    Path(".env"),
  ]
  found = [str(p) for p in candidates if p.is_file()]
  return tuple(found) if found else (".env",)


class Settings(BaseSettings):
  # os.environ from Docker env_file takes precedence over env_file on disk
  model_config = SettingsConfigDict(
    env_file=_discover_env_files(),
    env_file_encoding="utf-8",
    extra="ignore",
  )

  gemini_api_key_1: Optional[str] = Field(default=None)
  gemini_api_key_2: Optional[str] = Field(default=None)
  gemini_api_key_3: Optional[str] = Field(default=None)
  tavily_api_key: Optional[str] = Field(default=None)

  secret_key: str = Field(default="dev-secret-key-change-in-production")
  algorithm: str = Field(default="HS256")
  access_token_expire_minutes: int = Field(default=60)

  chroma_persist_path: str = Field(default="./chroma_db")

  app_env: str = Field(default="development")
  backend_host: str = Field(default="0.0.0.0")
  backend_port: int = Field(default=8000)
  frontend_url: str = Field(default="http://localhost:3000")

  gmail_sender: Optional[str] = Field(default=None)
  gmail_app_password: Optional[str] = Field(default=None)
  notification_email: Optional[str] = Field(default=None)

  def get_gemini_keys(self) -> list[str]:
    keys = [
      self.gemini_api_key_1,
      self.gemini_api_key_2,
      self.gemini_api_key_3,
    ]
    env_keys = [
      os.getenv("GEMINI_API_KEY_1"),
      os.getenv("GEMINI_API_KEY_2"),
      os.getenv("GEMINI_API_KEY_3"),
    ]
    merged = keys + env_keys
    valid: list[str] = []
    for k in merged:
      if not k or not str(k).strip():
        continue
      key = str(k).strip()
      lower = key.lower()
      if "your_gemini" in lower or lower.endswith("_here") or key.startswith("sk-placeholder"):
        continue
      valid.append(key)
    return list(dict.fromkeys(valid))

  def has_gemini_keys(self) -> bool:
    return len(self.get_gemini_keys()) > 0


@lru_cache
def get_settings() -> Settings:
  return Settings()


settings = get_settings()
