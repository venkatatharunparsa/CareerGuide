import sys
import time
from statistics import mean

import httpx

BASE = "http://localhost:8000"


def wait_for_backend(timeout: float = 90.0) -> bool:
  deadline = time.time() + timeout
  while time.time() < deadline:
    try:
      r = httpx.get(f"{BASE}/health", timeout=5)
      if r.status_code == 200:
        return True
    except Exception:
      pass
    time.sleep(2)
  return False
USER = "smoketest"
PASS = "smokepass123"


def _ok(name: str, condition: bool, detail: str = "") -> bool:
  status = "PASS" if condition else "FAIL"
  suffix = f" — {detail}" if detail else ""
  print(f"[{status}] {name}{suffix}")
  return condition


def main() -> int:
  print("=== Full System Test ===")
  all_ok = True

  if not wait_for_backend():
    print("[FAIL] Backend not ready")
    return 1

  r = httpx.get(f"{BASE}/health", timeout=20)
  all_ok &= _ok("Health", r.status_code == 200, str(r.status_code))

  r = httpx.post(
    f"{BASE}/api/auth/token",
    data={"username": USER, "password": PASS},
    headers={"Content-Type": "application/x-www-form-urlencoded"},
    timeout=30,
  )
  all_ok &= _ok("Login", r.status_code == 200, str(r.status_code))
  if r.status_code != 200:
    return 1
  token = r.json().get("access_token")
  H = {"Authorization": f"Bearer {token}"}

  profile_payload = {
    "skills": '["Python","FastAPI","React","Docker","LangChain"]',
    "target_roles": '["Backend Developer","AI Engineer"]',
    "experience_years": "2",
    "bio": "Backend developer building AI-enabled web services.",
  }
  r = httpx.post(f"{BASE}/api/profile/update", data=profile_payload, headers=H, timeout=90)
  total_skills = 0
  if r.status_code == 200:
    total_skills = int(r.json().get("total_skills", 0))
  all_ok &= _ok(
    "Profile Update",
    r.status_code == 200,
    f"{r.status_code}, total_skills={total_skills}",
  )

  r = httpx.post(
    f"{BASE}/api/profile/project/add",
    data={
      "name": "Job Agent",
      "description": "LLM powered job matching app",
      "tech_stack": '["Python","FastAPI","React","LangChain"]',
      "url": "https://github.com/example/job-agent",
    },
    headers=H,
    timeout=60,
  )
  all_ok &= _ok("Project Add", r.status_code == 200, str(r.status_code))

  r = httpx.get(f"{BASE}/api/profile/", headers=H, timeout=30)
  pdata = r.json() if r.status_code == 200 else {}
  all_ok &= _ok(
    "Profile Fields",
    r.status_code == 200
    and isinstance(pdata.get("skills"), list)
    and isinstance(pdata.get("all_skills"), list)
    and isinstance(pdata.get("target_roles"), list)
    and isinstance(pdata.get("projects"), list),
    f"{r.status_code}, all_skills={len(pdata.get('all_skills', []))}",
  )

  r = httpx.post(f"{BASE}/api/agents/run", headers=H, timeout=180)
  adata = r.json() if r.status_code == 200 else {}
  all_ok &= _ok("Agent Run", r.status_code == 200, f"{r.status_code}, jobs={adata.get('total_jobs',0)}")

  r = httpx.get(f"{BASE}/api/jobs/", headers=H, timeout=60)
  jobs = r.json() if r.status_code == 200 else []
  all_ok &= _ok("Jobs Fetch", r.status_code == 200 and len(jobs) > 0, f"{r.status_code}, count={len(jobs)}")
  if jobs:
    shape_ok = all(
      isinstance(j.get("matched_skills", []), list)
      and isinstance(j.get("missing_skills", []), list)
      and isinstance(j.get("skill_gaps", []), list)
      and isinstance(j.get("learning_suggestions", []), list)
      and isinstance(j.get("match_reason", ""), str)
      for j in jobs[:5]
    )
    avg_score = int(mean([int(j.get("match_score", 0)) for j in jobs])) if jobs else 0
    all_ok &= _ok("Scoring Shape", shape_ok, f"avg={avg_score}%")

  r = httpx.post(f"{BASE}/api/jobs/tailor-resume/0", headers=H, timeout=180)
  tdata = r.json() if r.status_code == 200 else {}
  pdf_b64 = tdata.get("pdf_base64", "")
  tailor_ok = (
    r.status_code == 200
    and bool(pdf_b64)
    and isinstance(tdata.get("ats_score"), int)
    and bool(tdata.get("template_used"))
  )
  all_ok &= _ok(
    "Tailor Resume",
    tailor_ok,
    f"{r.status_code}, ats={tdata.get('ats_score')}, b64={len(pdf_b64)}",
  )

  print("=== Full System Result ===")
  print("PASS" if all_ok else "FAIL")
  return 0 if all_ok else 1


if __name__ == "__main__":
  sys.exit(main())

