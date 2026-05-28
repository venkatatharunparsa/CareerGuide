import json
import sys

import httpx

BASE = "http://localhost:8000"
USER = "persist_test2"
PASS = "testpass123"


def login():
  r = httpx.post(
    f"{BASE}/api/auth/token",
    data={"username": USER, "password": PASS},
    headers={"Content-Type": "application/x-www-form-urlencoded"},
    timeout=30,
  )
  r.raise_for_status()
  return {"Authorization": f"Bearer {r.json()['access_token']}"}


def save_profile(H):
  httpx.post(
    f"{BASE}/api/profile/update",
    data={
      "skills": json.dumps(["Python", "FastAPI"]),
      "target_roles": json.dumps(["Backend Dev"]),
    },
    headers=H,
    timeout=60,
  )


def main():
  if len(sys.argv) > 1 and sys.argv[1] == "after":
    H = login()
    prof = httpx.get(f"{BASE}/api/profile/", headers=H, timeout=30).json()
    jobs = httpx.get(f"{BASE}/api/jobs/", headers=H, timeout=30).json()
    print("after restart skills:", prof.get("skills"))
    print("jobs count:", len(jobs))
    sources = sorted({j.get("source", "") for j in jobs if j.get("source")})
    print("sources:", sources)
    return

  httpx.post(
    f"{BASE}/api/auth/register",
    json={"username": USER, "password": PASS},
    timeout=30,
  )
  H = login()
  save_profile(H)
  prof = httpx.get(f"{BASE}/api/profile/", headers=H, timeout=30).json()
  print("before restart skills:", prof.get("skills"))


if __name__ == "__main__":
  main()
