import logging
from typing import Optional

from app.config import get_settings
from app.utils.key_rotator import get_key_rotator

logger = logging.getLogger(__name__)


class GeminiService:
  def __init__(self):
    self.rotator = get_key_rotator()
    self.settings = get_settings()
    self.model_name = "gemini-2.0-flash"

  def _get_llm(self, api_key: str):
    from langchain_google_genai import ChatGoogleGenerativeAI

    return ChatGoogleGenerativeAI(
      model=self.model_name,
      google_api_key=api_key,
      temperature=0.3,
      request_timeout=15,
      max_retries=0,
    )

  async def chat(self, prompt: str, max_attempts: int = 2) -> str:
    if not self.rotator.has_keys():
      logger.warning("No Gemini keys — returning mock response")
      return self._mock_response(prompt)

    attempts = min(max_attempts, max(self.rotator._total, 1))
    last_error = None
    for attempt in range(attempts):
      try:
        key = self.rotator.get_next_key()
        if not key:
          return self._mock_response(prompt)
        llm = self._get_llm(key)
        from langchain_core.messages import HumanMessage

        response = await llm.ainvoke([HumanMessage(content=prompt)])
        content = response.content
        return content if isinstance(content, str) else str(content)
      except Exception as e:
        last_error = e
        err_str = str(e).lower()
        if "429" in err_str or "quota" in err_str or "rate" in err_str:
          logger.warning("Rate limit hit, rotating key. Attempt %d", attempt + 1)
          continue
        if "api_key_invalid" in err_str or "api key not valid" in err_str:
          logger.warning("Invalid Gemini key, rotating. Attempt %d", attempt + 1)
          continue
        logger.error("Gemini error: %s", e)
        raise

    logger.error("All Gemini keys exhausted: %s", last_error)
    return self._mock_response(prompt)

  async def chat_with_context(self, system: str, human: str) -> str:
    combined = f"{system}\n\n{human}"
    return await self.chat(combined)

  def _mock_response(self, prompt: str) -> str:
    """Deterministic mock for development when no API keys set."""
    if "plan" in prompt.lower() or "instruct" in prompt.lower():
      return """{
                "sites": [
                    {"url": "https://www.linkedin.com/jobs", "query": "software engineer", "seniority": "mid"},
                    {"url": "https://www.naukri.com", "query": "backend developer", "seniority": "mid"},
                    {"url": "https://internshala.com", "query": "python developer internship", "seniority": "entry"}
                ]
            }"""
    if "score" in prompt.lower() or "match" in prompt.lower():
      return """{
                "scores": [85, 72, 68],
                "summary": "Good matches found for your profile. Top match is a Python backend role."
            }"""
    if "extract" in prompt.lower() and "skill" in prompt.lower():
      return '["Docker", "PostgreSQL", "REST API", "System Design"]'
    if "ats" in prompt.lower() or "resume" in prompt.lower():
      return """SUMMARY
Results-driven software engineer with Python, FastAPI, and React experience. Seeking backend and ML roles.

SKILLS
Python, FastAPI, React, LangChain, REST APIs, Docker, Git

EXPERIENCE
Software Engineer — Built API services and React dashboards; integrated LLM workflows with LangChain.

EDUCATION
Bachelor's in Computer Science"""
    return "Mock Gemini response — add your API keys to .env to enable real AI responses."


_gemini_service: Optional[GeminiService] = None


def get_gemini_service() -> GeminiService:
  global _gemini_service
  if _gemini_service is None:
    _gemini_service = GeminiService()
  return _gemini_service
