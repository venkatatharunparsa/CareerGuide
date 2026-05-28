import json
import logging
import re
from typing import List

logger = logging.getLogger(__name__)

TECH_SKILLS = [
  "Python",
  "JavaScript",
  "TypeScript",
  "Java",
  "C++",
  "C#",
  "Go",
  "Rust",
  "Ruby",
  "PHP",
  "Swift",
  "Kotlin",
  "Scala",
  "R",
  "MATLAB",
  "Dart",
  "Elixir",
  "React",
  "Vue",
  "Angular",
  "Next.js",
  "Svelte",
  "HTML",
  "CSS",
  "TailwindCSS",
  "Bootstrap",
  "Redux",
  "GraphQL",
  "React Native",
  "Flutter",
  "FastAPI",
  "Django",
  "Flask",
  "Node.js",
  "Express",
  "Spring Boot",
  "Laravel",
  "Rails",
  "NestJS",
  "Gin",
  "Echo",
  "Fiber",
  "PostgreSQL",
  "MySQL",
  "MongoDB",
  "Redis",
  "SQLite",
  "Cassandra",
  "DynamoDB",
  "Supabase",
  "Firebase",
  "Elasticsearch",
  "Pinecone",
  "Weaviate",
  "AWS",
  "GCP",
  "Azure",
  "Docker",
  "Kubernetes",
  "Terraform",
  "Ansible",
  "CI/CD",
  "GitHub Actions",
  "Jenkins",
  "Nginx",
  "Linux",
  "Prometheus",
  "Grafana",
  "Machine Learning",
  "Deep Learning",
  "NLP",
  "LangChain",
  "LangGraph",
  "PyTorch",
  "TensorFlow",
  "Scikit-learn",
  "Pandas",
  "NumPy",
  "Matplotlib",
  "RAG",
  "LLM",
  "OpenAI",
  "Gemini",
  "Claude",
  "Hugging Face",
  "BERT",
  "GPT",
  "Computer Vision",
  "OpenCV",
  "YOLO",
  "Stable Diffusion",
  "Langsmith",
  "Git",
  "GitHub",
  "GitLab",
  "Jira",
  "Figma",
  "Postman",
  "VS Code",
  "Jupyter",
  "Airflow",
  "Kafka",
  "RabbitMQ",
  "Celery",
  "Spark",
  "Hadoop",
  "REST API",
  "gRPC",
  "Microservices",
  "System Design",
  "Agile",
  "Scrum",
  "Data Structures",
  "Algorithms",
  "OOP",
  "Functional Programming",
  "Blockchain",
  "Solidity",
  "Web3",
  "Unity",
  "Unreal Engine",
  "Selenium",
  "Playwright",
  "BeautifulSoup",
  "Scrapy",
  "XGBoost",
  "LightGBM",
]


def extract_skills_from_text(text: str) -> List[str]:
  if not text:
    return []
  text_lower = text.lower()
  found = []
  for skill in TECH_SKILLS:
    pattern = r"\b" + re.escape(skill.lower()) + r"\b"
    if re.search(pattern, text_lower):
      found.append(skill)
  return list(dict.fromkeys(found))


async def extract_skills_with_gemini(text: str, existing: list) -> List[str]:
  try:
    from app.services.gemini_service import get_gemini_service

    import asyncio

    gemini = get_gemini_service()
    prompt = f"""Extract ALL technical skills, tools, frameworks,
languages from this text. Be comprehensive.

Text:
{text[:3000]}

Already found (skip): {existing[:30]}

Return ONLY a JSON array of skill name strings.
Example: ["FastAPI","PostgreSQL","System Design"]"""
    resp = await asyncio.wait_for(gemini.chat(prompt), timeout=20.0)
    clean = re.sub(r"```json|```", "", resp).strip()
    s = clean.find("[")
    e = clean.rfind("]") + 1
    if s >= 0 and e > s:
      extra = json.loads(clean[s:e])
      return [
        x
        for x in extra
        if isinstance(x, str) and 1 < len(x) < 60 and x not in existing
      ]
  except Exception as ex:
    logger.warning("Gemini skill extract failed: %s", ex)
  return []


def extract_from_project(project: dict) -> List[str]:
  text = (
    project.get("description", "")
    + " "
    + project.get("outcome", "")
    + " "
    + project.get("role", "")
    + " "
    + " ".join(project.get("tech_stack", []))
  )
  return extract_skills_from_text(text)


def extract_from_experience(exp: dict) -> List[str]:
  text = (
    exp.get("description", "")
    + " "
    + exp.get("title", "")
    + " "
    + " ".join(exp.get("skills_used", []))
  )
  return extract_skills_from_text(text)


async def build_master_skill_set(
  username: str,
  manual_skills: list,
  resume_text: str,
  projects: list,
  experiences: list,
) -> List[str]:
  """Build deduplicated master skill set from all sources."""
  all_skills = set(manual_skills)
  all_skills.update(extract_skills_from_text(resume_text))
  for p in projects:
    all_skills.update(extract_from_project(p))
  for e in experiences:
    all_skills.update(extract_from_experience(e))
  combined_text = (resume_text + " " + " ".join(
    [p.get("description", "") for p in projects]
  )).strip()
  gemini_skills = []
  if len(combined_text) > 40:
    gemini_skills = await extract_skills_with_gemini(
      combined_text, list(all_skills)
    )
  all_skills.update(gemini_skills)
  return sorted(all_skills)
