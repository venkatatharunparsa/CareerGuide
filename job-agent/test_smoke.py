"""
Job Agent — smoke test
Run from repo root: python test_smoke.py
Backend must be running on http://localhost:8000
"""
import json
import sys
import time

try:
  import httpx
except ImportError:
  print("Installing httpx...")
  import subprocess

  subprocess.check_call([sys.executable, "-m", "pip", "install", "httpx"])
  import httpx

BASE = "http://localhost:8000"


def check(name, r, expected_status=200):
  ok = r.status_code == expected_status
  print(f"{'[OK]' if ok else '[FAIL]'} {name}: {r.status_code}")
  if not ok:
    print(f"  Response: {r.text[:300]}")
  return ok, r


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


def run():
  print("\n=== Job Agent Smoke Test ===\n")
  all_pass = True

  if not wait_for_backend():
    print("[FAIL] Backend not ready")
    return False

  ok, r = check("Health check", httpx.get(f"{BASE}/health"))
  all_pass &= ok

  reg = httpx.post(
    f"{BASE}/api/auth/register",
    json={"username": "smoketest", "password": "smokepass123"},
  )
  reg_ok = reg.status_code in (201, 400)
  print(
    f"{'[OK]' if reg_ok else '[FAIL]'} Register user: {reg.status_code}"
    + (" (already exists)" if reg.status_code == 400 else "")
  )
  all_pass &= reg_ok

  ok, r = check(
    "Login",
    httpx.post(
      f"{BASE}/api/auth/token",
      data={"username": "smoketest", "password": "smokepass123"},
      headers={"Content-Type": "application/x-www-form-urlencoded"},
    ),
  )
  all_pass &= ok
  token = r.json().get("access_token", "") if ok else ""

  if not token:
    print("  Skipping auth tests — no token received")
    return False

  H = {"Authorization": f"Bearer {token}"} if token else {}

  ok, r = check("Auth /me", httpx.get(f"{BASE}/api/auth/me", headers=H))
  all_pass &= ok

  ok, r = check(
    "Update profile",
    httpx.post(
      f"{BASE}/api/profile/update",
      data={
        "skills": json.dumps(["Python", "FastAPI", "React", "LangChain"]),
        "target_roles": json.dumps(["Backend Developer", "ML Engineer"]),
      },
      headers=H,
      timeout=90.0,
    ),
  )
  all_pass &= ok

  ok, r = check("Get profile", httpx.get(f"{BASE}/api/profile/", headers=H))
  all_pass &= ok

  print("\n  Running agent (180s timeout)...")
  ok, r = check(
    "Run agent",
    httpx.post(f"{BASE}/api/agents/run", headers=H, timeout=180.0),
  )
  all_pass &= ok
  if ok:
    data = r.json()
    print(
      f"  -> {data.get('total_jobs', 0)} jobs found, "
      f"avg score {data.get('avg_score', 0)}%, "
      f"status: {data.get('status')}"
    )

  ok, r = check("Get jobs", httpx.get(f"{BASE}/api/jobs/", headers=H))
  all_pass &= ok
  if ok:
    jobs = r.json()
    print(f"  -> {len(jobs)} jobs in store")
    if jobs:
      j = jobs[0]
      print(
        f"  -> Top job: {j.get('title')} at {j.get('company')} "
        f"({j.get('match_score')}% match)"
      )

  print(f"\n=== {'ALL TESTS PASSED' if all_pass else 'SOME TESTS FAILED'} ===\n")
  return all_pass


if __name__ == "__main__":
  sys.exit(0 if run() else 1)
