"""
Shared in-memory store.
All routers import from here — avoids circular imports.
This will be replaced by a real database in production.
"""

# username -> profile data
profiles_db: dict[str, dict] = {}

# username -> list of jobs from last agent run
agent_results_db: dict[str, list] = {}

# username -> saved jobs
saved_jobs_db: dict[str, list] = {}

# username -> hashed user record
users_db: dict[str, dict] = {}
