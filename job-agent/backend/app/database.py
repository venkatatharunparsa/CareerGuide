import json
import os
import sqlite3
from pathlib import Path

DB_PATH = os.getenv("SQLITE_DB_PATH", "/chroma_db/jobagent.db")


def get_db():
  Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
  conn = sqlite3.connect(DB_PATH, check_same_thread=False, timeout=30)
  conn.row_factory = sqlite3.Row
  conn.execute("PRAGMA journal_mode=WAL")
  return conn


def init_db():
  conn = get_db()
  conn.executescript(
    """
    CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY,
        hashed_password TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS user_profiles (
        username TEXT PRIMARY KEY,
        skills TEXT DEFAULT '[]',
        target_roles TEXT DEFAULT '[]',
        experience_years INTEGER DEFAULT 1,
        bio TEXT DEFAULT '',
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (username) REFERENCES users(username)
    );

    CREATE TABLE IF NOT EXISTS resumes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        filename TEXT,
        raw_text TEXT DEFAULT '',
        extracted_skills TEXT DEFAULT '[]',
        uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        is_primary INTEGER DEFAULT 0,
        FOREIGN KEY (username) REFERENCES users(username)
    );

    CREATE TABLE IF NOT EXISTS user_projects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        name TEXT,
        description TEXT DEFAULT '',
        tech_stack TEXT DEFAULT '[]',
        url TEXT DEFAULT '',
        role TEXT DEFAULT '',
        outcome TEXT DEFAULT '',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (username) REFERENCES users(username)
    );

    CREATE TABLE IF NOT EXISTS user_experiences (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        type TEXT DEFAULT 'job',
        title TEXT,
        organization TEXT,
        description TEXT DEFAULT '',
        skills_used TEXT DEFAULT '[]',
        start_date TEXT DEFAULT '',
        end_date TEXT DEFAULT '',
        is_current INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (username) REFERENCES users(username)
    );

    CREATE TABLE IF NOT EXISTS job_cache (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        title TEXT,
        company TEXT,
        location TEXT DEFAULT '',
        url TEXT,
        description TEXT DEFAULT '',
        source TEXT DEFAULT '',
        job_type TEXT DEFAULT 'full-time',
        raw_data TEXT DEFAULT '{}',
        scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (username) REFERENCES users(username)
    );

    CREATE TABLE IF NOT EXISTS evaluated_jobs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        cache_id INTEGER,
        title TEXT,
        company TEXT,
        location TEXT DEFAULT '',
        url TEXT,
        description TEXT DEFAULT '',
        source TEXT DEFAULT '',
        job_type TEXT DEFAULT 'full-time',
        match_score INTEGER DEFAULT 0,
        match_reason TEXT DEFAULT '',
        matched_skills TEXT DEFAULT '[]',
        missing_skills TEXT DEFAULT '[]',
        skill_gaps TEXT DEFAULT '[]',
        learning_suggestions TEXT DEFAULT '[]',
        posted_date TEXT DEFAULT '',
        evaluated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (username) REFERENCES users(username)
    );

    CREATE TABLE IF NOT EXISTS saved_jobs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        job_data TEXT NOT NULL,
        saved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS tailored_resumes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        job_title TEXT,
        job_company TEXT,
        job_url TEXT DEFAULT '',
        latex_code TEXT DEFAULT '',
        resume_text TEXT DEFAULT '',
        ats_score INTEGER DEFAULT 0,
        template_used TEXT DEFAULT '',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (username) REFERENCES users(username)
    );
    """
  )
  _migrate_legacy_schema(conn)
  conn.commit()
  conn.close()


def _migrate_legacy_schema(conn):
  """Migrate data from old profiles/jobs tables if present."""
  tables = {
    r[0]
    for r in conn.execute(
      "SELECT name FROM sqlite_master WHERE type='table'"
    ).fetchall()
  }
  if "profiles" in tables:
    try:
      rows = conn.execute("SELECT * FROM profiles").fetchall()
      for row in rows:
        d = dict(row)
        conn.execute(
          """
          INSERT INTO user_profiles (username, skills, target_roles,
            experience_years, bio)
          VALUES (?, ?, ?, ?, ?)
          ON CONFLICT(username) DO UPDATE SET
            skills=excluded.skills,
            target_roles=excluded.target_roles,
            experience_years=excluded.experience_years,
            bio=excluded.bio
          """,
          (
            d["username"],
            d.get("skills", "[]"),
            d.get("target_roles", "[]"),
            d.get("experience_years", 1),
            d.get("bio", "") or "",
          ),
        )
        resume_text = d.get("resume_text", "") or ""
        if resume_text:
          conn.execute(
            """
            INSERT INTO resumes (username, filename, raw_text,
              extracted_skills, is_primary)
            SELECT ?, 'migrated.txt', ?, '[]', 1
            WHERE NOT EXISTS (
              SELECT 1 FROM resumes WHERE username=? AND is_primary=1
            )
            """,
            (d["username"], resume_text, d["username"]),
          )
        projects_raw = d.get("projects")
        if projects_raw:
          try:
            projects = json.loads(projects_raw)
            for p in projects:
              if not isinstance(p, dict):
                continue
              conn.execute(
                """
                INSERT INTO user_projects
                  (username, name, description, tech_stack, url, role, outcome)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                  d["username"],
                  p.get("name", ""),
                  p.get("description", ""),
                  json.dumps(p.get("tech_stack", [])),
                  p.get("url", ""),
                  p.get("role", ""),
                  p.get("outcome", ""),
                ),
              )
          except Exception:
            pass
    except Exception:
      pass

  if "jobs" in tables:
    try:
      count = conn.execute("SELECT COUNT(*) FROM evaluated_jobs").fetchone()[0]
      if count == 0:
        conn.execute(
          """
          INSERT INTO evaluated_jobs (
            username, title, company, location, url, description,
            source, job_type, match_score, match_reason,
            matched_skills, missing_skills, posted_date
          )
          SELECT username, title, company, location, url, description,
            source, job_type, match_score, match_reason,
            matched_skills, missing_skills, posted_date
          FROM jobs
          """
        )
    except Exception:
      pass


# ── USER ──────────────────────────────────────────
def create_user(username, hashed_password):
  try:
    conn = get_db()
    conn.execute(
      "INSERT INTO users (username,hashed_password) VALUES (?,?)",
      (username, hashed_password),
    )
    conn.commit()
    conn.close()
    return True
  except sqlite3.IntegrityError:
    return False


def get_user(username):
  conn = get_db()
  row = conn.execute(
    "SELECT * FROM users WHERE username=?", (username,)
  ).fetchone()
  conn.close()
  return dict(row) if row else None


# ── PROFILE ───────────────────────────────────────
def save_profile(username, skills, target_roles, experience_years=1, bio=""):
  conn = get_db()
  conn.execute(
    """
        INSERT INTO user_profiles
            (username,skills,target_roles,experience_years,bio)
        VALUES (?,?,?,?,?)
        ON CONFLICT(username) DO UPDATE SET
            skills=excluded.skills,
            target_roles=excluded.target_roles,
            experience_years=excluded.experience_years,
            bio=excluded.bio,
            updated_at=CURRENT_TIMESTAMP
    """,
    (username, json.dumps(skills), json.dumps(target_roles), experience_years, bio),
  )
  conn.commit()
  conn.close()


def get_profile(username):
  conn = get_db()
  row = conn.execute(
    "SELECT * FROM user_profiles WHERE username=?",
    (username,),
  ).fetchone()
  conn.close()
  if not row:
    return None
  p = dict(row)
  p["skills"] = json.loads(p.get("skills", "[]"))
  p["target_roles"] = json.loads(p.get("target_roles", "[]"))
  return p


def get_full_profile(username):
  """Returns complete user profile with resumes, projects, experiences."""
  profile = get_profile(username) or {
    "username": username,
    "skills": [],
    "target_roles": [],
    "experience_years": 1,
    "bio": "",
  }
  profile["resumes"] = get_resumes(username)
  profile["projects"] = get_projects(username)
  profile["experiences"] = get_experiences(username)

  all_skills = set(profile["skills"])
  for r in profile["resumes"]:
    all_skills.update(r.get("extracted_skills", []))
  for p in profile["projects"]:
    all_skills.update(p.get("tech_stack", []))
  for e in profile["experiences"]:
    all_skills.update(e.get("skills_used", []))
  profile["all_skills"] = sorted(all_skills)

  primary = next(
    (r for r in profile["resumes"] if r.get("is_primary")),
    profile["resumes"][0] if profile["resumes"] else None,
  )
  profile["resume_text"] = primary["raw_text"] if primary else ""
  return profile


# ── RESUMES ───────────────────────────────────────
def save_resume(username, filename, raw_text, extracted_skills, set_primary=False):
  conn = get_db()
  if set_primary:
    conn.execute(
      "UPDATE resumes SET is_primary=0 WHERE username=?",
      (username,),
    )
  conn.execute(
    """
        INSERT INTO resumes
            (username,filename,raw_text,extracted_skills,is_primary)
        VALUES (?,?,?,?,?)
    """,
    (
      username,
      filename,
      raw_text,
      json.dumps(extracted_skills),
      1 if set_primary else 0,
    ),
  )
  conn.commit()
  conn.close()


def get_resumes(username):
  conn = get_db()
  rows = conn.execute(
    "SELECT * FROM resumes WHERE username=? ORDER BY uploaded_at DESC",
    (username,),
  ).fetchall()
  conn.close()
  result = []
  for r in rows:
    d = dict(r)
    d["extracted_skills"] = json.loads(d.get("extracted_skills", "[]"))
    result.append(d)
  return result


def set_primary_resume(username, resume_id):
  conn = get_db()
  conn.execute(
    "UPDATE resumes SET is_primary=0 WHERE username=?", (username,)
  )
  conn.execute(
    "UPDATE resumes SET is_primary=1 WHERE id=? AND username=?",
    (resume_id, username),
  )
  conn.commit()
  conn.close()


def delete_resume(username, resume_id):
  conn = get_db()
  conn.execute(
    "DELETE FROM resumes WHERE id=? AND username=?",
    (resume_id, username),
  )
  conn.commit()
  conn.close()


# ── PROJECTS ──────────────────────────────────────
def save_project(username, name, description, tech_stack, url="", role="", outcome=""):
  conn = get_db()
  conn.execute(
    """
        INSERT INTO user_projects
            (username,name,description,tech_stack,url,role,outcome)
        VALUES (?,?,?,?,?,?,?)
    """,
    (username, name, description, json.dumps(tech_stack), url, role, outcome),
  )
  conn.commit()
  conn.close()


def get_projects(username):
  conn = get_db()
  rows = conn.execute(
    "SELECT * FROM user_projects WHERE username=? ORDER BY created_at DESC",
    (username,),
  ).fetchall()
  conn.close()
  result = []
  for r in rows:
    d = dict(r)
    d["tech_stack"] = json.loads(d.get("tech_stack", "[]"))
    result.append(d)
  return result


def update_project(username, project_id, **fields):
  conn = get_db()
  for k, v in fields.items():
    if k == "tech_stack":
      v = json.dumps(v)
    conn.execute(
      f"UPDATE user_projects SET {k}=? WHERE id=? AND username=?",
      (v, project_id, username),
    )
  conn.commit()
  conn.close()


def delete_project(username, project_id):
  conn = get_db()
  conn.execute(
    "DELETE FROM user_projects WHERE id=? AND username=?",
    (project_id, username),
  )
  conn.commit()
  conn.close()


# ── EXPERIENCES ───────────────────────────────────
def save_experience(
  username,
  exp_type,
  title,
  organization,
  description,
  skills_used,
  start_date,
  end_date="",
  is_current=False,
):
  conn = get_db()
  conn.execute(
    """
        INSERT INTO user_experiences
            (username,type,title,organization,description,
             skills_used,start_date,end_date,is_current)
        VALUES (?,?,?,?,?,?,?,?,?)
    """,
    (
      username,
      exp_type,
      title,
      organization,
      description,
      json.dumps(skills_used),
      start_date,
      end_date,
      1 if is_current else 0,
    ),
  )
  conn.commit()
  conn.close()


def get_experiences(username):
  conn = get_db()
  rows = conn.execute(
    """
        SELECT * FROM user_experiences WHERE username=?
           ORDER BY is_current DESC, start_date DESC
        """,
    (username,),
  ).fetchall()
  conn.close()
  result = []
  for r in rows:
    d = dict(r)
    d["skills_used"] = json.loads(d.get("skills_used", "[]"))
    result.append(d)
  return result


def delete_experience(username, exp_id):
  conn = get_db()
  conn.execute(
    "DELETE FROM user_experiences WHERE id=? AND username=?",
    (exp_id, username),
  )
  conn.commit()
  conn.close()


# ── JOB CACHE ─────────────────────────────────────
def cache_jobs(username, jobs):
  conn = get_db()
  conn.execute("DELETE FROM job_cache WHERE username=?", (username,))
  for j in jobs:
    conn.execute(
      """
            INSERT INTO job_cache
                (username,title,company,location,url,
                 description,source,job_type,raw_data)
            VALUES (?,?,?,?,?,?,?,?,?)
        """,
      (
        username,
        j.get("title", ""),
        j.get("company", ""),
        j.get("location", ""),
        j.get("url", ""),
        j.get("description", ""),
        j.get("source", ""),
        j.get("job_type", "full-time"),
        json.dumps(j),
      ),
    )
  conn.commit()
  conn.close()


def get_cached_jobs(username):
  conn = get_db()
  rows = conn.execute(
    "SELECT * FROM job_cache WHERE username=?",
    (username,),
  ).fetchall()
  conn.close()
  return [dict(r) for r in rows]


# ── EVALUATED JOBS ────────────────────────────────
def save_evaluated_jobs(username, jobs):
  conn = get_db()
  conn.execute("DELETE FROM evaluated_jobs WHERE username=?", (username,))
  for j in jobs:
    conn.execute(
      """
            INSERT INTO evaluated_jobs
                (username,title,company,location,url,description,
                 source,job_type,match_score,match_reason,
                 matched_skills,missing_skills,skill_gaps,
                 learning_suggestions,posted_date)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """,
      (
        username,
        j.get("title", ""),
        j.get("company", ""),
        j.get("location", ""),
        j.get("url", ""),
        j.get("description", ""),
        j.get("source", ""),
        j.get("job_type", "full-time"),
        j.get("match_score", 0),
        j.get("match_reason", ""),
        json.dumps(j.get("matched_skills", [])),
        json.dumps(j.get("missing_skills", [])),
        json.dumps(j.get("skill_gaps", [])),
        json.dumps(j.get("learning_suggestions", [])),
        j.get("posted_date", ""),
      ),
    )
  conn.commit()
  conn.close()


def get_evaluated_jobs(username):
  conn = get_db()
  rows = conn.execute(
    """
        SELECT * FROM evaluated_jobs WHERE username=?
           ORDER BY match_score DESC
        """,
    (username,),
  ).fetchall()
  conn.close()
  result = []
  for r in rows:
    d = dict(r)
    for f in [
      "matched_skills",
      "missing_skills",
      "skill_gaps",
      "learning_suggestions",
    ]:
      d[f] = json.loads(d.get(f, "[]"))
    result.append(d)
  return result


def save_job_bookmark(username, job_data):
  conn = get_db()
  conn.execute(
    "INSERT INTO saved_jobs (username,job_data) VALUES (?,?)",
    (username, json.dumps(job_data)),
  )
  conn.commit()
  conn.close()


def get_saved_jobs(username):
  conn = get_db()
  rows = conn.execute(
    "SELECT * FROM saved_jobs WHERE username=? ORDER BY saved_at DESC",
    (username,),
  ).fetchall()
  conn.close()
  return [json.loads(r["job_data"]) for r in rows]


# ── TAILORED RESUMES ──────────────────────────────
def save_tailored_resume(
  username,
  job_title,
  job_company,
  job_url,
  latex_code,
  resume_text,
  ats_score,
  template_used,
):
  conn = get_db()
  conn.execute(
    """
        INSERT INTO tailored_resumes
            (username,job_title,job_company,job_url,
             latex_code,resume_text,ats_score,template_used)
        VALUES (?,?,?,?,?,?,?,?)
    """,
    (
      username,
      job_title,
      job_company,
      job_url,
      latex_code,
      resume_text,
      ats_score,
      template_used,
    ),
  )
  last_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
  conn.commit()
  conn.close()
  return last_id


def get_tailored_resumes(username):
  conn = get_db()
  rows = conn.execute(
    """
        SELECT * FROM tailored_resumes WHERE username=?
           ORDER BY created_at DESC
        """,
    (username,),
  ).fetchall()
  conn.close()
  return [dict(r) for r in rows]


# backwards compat aliases
def save_jobs(username, jobs):
  save_evaluated_jobs(username, jobs)


def get_jobs(username):
  return get_evaluated_jobs(username)
