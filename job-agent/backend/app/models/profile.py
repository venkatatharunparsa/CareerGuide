from pydantic import BaseModel, Field


class ProfileCreate(BaseModel):
  skills: list[str] = Field(default_factory=list)
  experience_years: float = 0
  education: list[str] = Field(default_factory=list)
  summary: str | None = None
  target_roles: list[str] = Field(default_factory=list)
  preferred_locations: list[str] = Field(default_factory=list)


class ProfileUpdate(BaseModel):
  skills: list[str] | None = None
  experience_years: float | None = None
  education: list[str] | None = None
  summary: str | None = None
  target_roles: list[str] | None = None
  preferred_locations: list[str] | None = None


class ProfileResponse(ProfileCreate):
  user_id: str
