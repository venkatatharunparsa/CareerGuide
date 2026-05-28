"""Phase 8 Round 3 — profile, agent, tailor upload test."""
import json
import sys

import httpx

BASE = "http://localhost:8000"

r = httpx.post(
    f"{BASE}/api/auth/token",
    data={"username": "smoketest", "password": "smokepass123"},
    headers={"Content-Type": "application/x-www-form-urlencoded"},
    timeout=30,
)
token = r.json()["access_token"]
H = {"Authorization": f"Bearer {token}"}

r = httpx.post(
    f"{BASE}/api/profile/update",
    data={
        "skills": json.dumps(
            ["Python", "FastAPI", "React", "Docker", "LangChain"]
        ),
        "target_roles": json.dumps(["Backend Developer", "ML Engineer"]),
        "experience_years": "2",
        "bio": "Building AI-powered applications with Python and FastAPI",
    },
    headers=H,
    timeout=90,
)
print("Profile update:", r.json())

r = httpx.post(
    f"{BASE}/api/profile/project/add",
    data={
        "name": "Job Agent",
        "description": "Agentic RAG system for job scraping with LangGraph and Gemini",
        "tech_stack": json.dumps(
            ["Python", "FastAPI", "LangGraph", "ChromaDB", "React"]
        ),
        "role": "Full Stack Developer",
        "outcome": "Production-ready application",
    },
    headers=H,
    timeout=60,
)
print("Project add:", r.json())

r = httpx.post(
    f"{BASE}/api/profile/experience/add",
    data={
        "exp_type": "internship",
        "title": "Python Developer Intern",
        "organization": "TechCorp",
        "description": "Built REST APIs with FastAPI and PostgreSQL",
        "skills_used": json.dumps(["Python", "FastAPI", "PostgreSQL"]),
        "start_date": "2023-06",
        "end_date": "2023-12",
    },
    headers=H,
    timeout=60,
)
print("Experience add:", r.json())

r = httpx.get(f"{BASE}/api/profile/", headers=H, timeout=30)
p = r.json()
print("Full profile:")
print("  Skills:", len(p.get("all_skills", [])), "total")
print("  Projects:", len(p.get("projects", [])))
print("  Experiences:", len(p.get("experiences", [])))
print("  Resumes:", len(p.get("resumes", [])))

print("Running agent...")
r = httpx.post(f"{BASE}/api/agents/run", headers=H, timeout=180)
d = r.json()
print("Agent:", d.get("total_jobs"), "jobs,", d.get("avg_score"), "% avg")
summary_txt = str(d.get("summary", "")).encode("ascii", "replace").decode(); print("Summary:", summary_txt)

r = httpx.get(f"{BASE}/api/jobs/", headers=H, timeout=60)
jobs = r.json()
if jobs:
    j = jobs[0]
    print("Top job:", j.get("title"), "@", j.get("company"))
    print("Score:", j.get("match_score"), "%")
    print("Matched:", j.get("matched_skills", [])[:5])
    print("Missing:", j.get("missing_skills", [])[:3])
    print("Gaps:", j.get("skill_gaps", [])[:3])
    print("Learn:", j.get("learning_suggestions", [])[:2])

print("Tailoring resume...")
r = httpx.post(f"{BASE}/api/jobs/tailor-resume/0", headers=H, timeout=180)
d = r.json()
print("ATS Score:", d.get("ats_score"))
print("Template:", d.get("template_used"))
print("Improvements:", d.get("improvements", [])[:2])
b64 = d.get("pdf_base64", "")
print("PDF size:", len(b64), "chars (base64)")
sys.exit(0 if b64 and d.get("ats_score") is not None else 1)
