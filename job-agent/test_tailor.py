import json

import httpx

BASE = "http://localhost:8000"
USER = "smoketest"
PASS = "smokepass123"


def main():
  r = httpx.post(
    f"{BASE}/api/auth/token",
    data={"username": USER, "password": PASS},
    headers={"Content-Type": "application/x-www-form-urlencoded"},
    timeout=30,
  )
  if r.status_code != 200:
    httpx.post(f"{BASE}/api/auth/register", json={"username": USER, "password": PASS})
    r = httpx.post(
      f"{BASE}/api/auth/token",
      data={"username": USER, "password": PASS},
      headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
  H = {"Authorization": f"Bearer {r.json()['access_token']}"}

  httpx.post(
    f"{BASE}/api/profile/update",
    data={
      "skills": json.dumps(["Python", "FastAPI"]),
      "target_roles": json.dumps(["Backend Developer"]),
    },
    headers=H,
    timeout=60,
  )

  jobs = httpx.get(f"{BASE}/api/jobs/", headers=H, timeout=30).json()
  print("jobs:", len(jobs))
  if not jobs:
    httpx.post(f"{BASE}/api/agents/run", headers=H, timeout=120000)
    jobs = httpx.get(f"{BASE}/api/jobs/", headers=H).json()
    print("jobs after agent:", len(jobs))

  r = httpx.post(f"{BASE}/api/jobs/tailor-resume/0", headers=H, timeout=120000)
  print("tailor status:", r.status_code)
  print("bytes:", len(r.content))
  print("content-type:", r.headers.get("content-type"))


if __name__ == "__main__":
  main()
