from datetime import datetime

from pydantic import BaseModel, Field, HttpUrl


class JobListing(BaseModel):
  title: str
  company: str
  location: str | None = None
  url: HttpUrl | str
  description: str | None = None
  posted_date: str | None = None
  source: str


class JobCreate(JobListing):
  user_id: str | None = None


class JobMatch(BaseModel):
  job: JobListing
  match_score: float = Field(ge=0, le=100)


class AgentRunRequest(BaseModel):
  user_id: str
  target_roles: list[str] = Field(default_factory=list)
  target_urls: list[str] = Field(default_factory=list)


class AgentRunResponse(BaseModel):
  status: str
  filtered_jobs: list[JobMatch] = Field(default_factory=list)
  monitoring_updates: list[str] = Field(default_factory=list)
  error: str | None = None
