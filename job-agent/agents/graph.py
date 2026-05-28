import logging
from typing import Any

from langgraph.graph import END, StateGraph

from agents.monitor_agent import monitor_node
from agents.planner_agent import planner_node
from agents.scraper_agent import scraper_node
from agents.state import AgentState

logger = logging.getLogger(__name__)

_MOCK_PROFILE = {
  "skills": ["Python", "FastAPI", "React"],
  "target_roles": ["Backend Developer", "Full Stack Engineer"],
  "experience_years": 2,
  "bio": "Mock profile for agent pipeline testing",
  "projects": [],
  "experiences": [],
  "all_skills": ["Python", "FastAPI", "React"],
  "resume_text": "",
}

_DEFAULT_URLS = [
  "https://www.linkedin.com/jobs",
  "https://www.naukri.com",
  "https://internshala.com",
]


def _route_after_planner(state: AgentState) -> str:
  if state.get("error"):
    return "end"
  return "scraper"


def _build_graph() -> StateGraph:
  graph = StateGraph(AgentState)

  graph.add_node("planner", planner_node)
  graph.add_node("scraper", scraper_node)
  graph.add_node("monitor", monitor_node)

  graph.set_entry_point("planner")
  graph.add_conditional_edges(
    "planner",
    _route_after_planner,
    {"scraper": "scraper", "end": END},
  )
  graph.add_edge("scraper", "monitor")
  graph.add_edge("monitor", END)

  return graph


job_agent_graph = _build_graph().compile()


async def run_agent(
  user_id: str,
  *,
  user_profile: dict | None = None,
  target_roles: list[str] | None = None,
  target_urls: list[str] | None = None,
) -> dict[str, Any]:
  """Invoke the LangGraph job agent pipeline for a user."""
  profile = user_profile if user_profile else dict(_MOCK_PROFILE)
  roles = target_roles or profile.get("target_roles") or _MOCK_PROFILE["target_roles"]
  urls = target_urls or _DEFAULT_URLS

  initial: AgentState = {
    "user_id": user_id,
    "user_profile": profile,
    "target_roles": roles,
    "target_urls": urls,
    "search_keywords": [],
    "scraped_jobs": [],
    "filtered_jobs": [],
    "scrape_instructions": {},
    "monitoring_updates": [],
    "error": None,
    "status": "started",
  }

  logger.info("Starting job agent graph for user %s", user_id)
  result = await job_agent_graph.ainvoke(initial)
  return dict(result)
