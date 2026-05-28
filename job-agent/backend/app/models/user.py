from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
  email: EmailStr
  password: str = Field(min_length=8)
  full_name: str | None = None


class UserResponse(BaseModel):
  id: str
  email: EmailStr
  full_name: str | None = None


class UserInDB(UserResponse):
  hashed_password: str


class Token(BaseModel):
  access_token: str
  token_type: str = "bearer"


class TokenPayload(BaseModel):
  sub: str | None = None
