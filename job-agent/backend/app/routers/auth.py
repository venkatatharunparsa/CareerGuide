from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, Field

from app.database import create_user, get_user
from app.dependencies import (
  create_access_token,
  get_current_username,
  get_password_hash,
  verify_password,
)

router = APIRouter()


class RegisterRequest(BaseModel):
  username: str = Field(min_length=3, max_length=64)
  password: str = Field(min_length=8)


class TokenResponse(BaseModel):
  access_token: str
  token_type: str = "bearer"


class UserInfo(BaseModel):
  username: str


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(body: RegisterRequest):
  hashed = get_password_hash(body.password)
  success = create_user(body.username, hashed)
  if not success:
    raise HTTPException(status_code=400, detail="Username already registered")
  return {"message": "registered"}


@router.post("/token", response_model=TokenResponse)
async def login(form: Annotated[OAuth2PasswordRequestForm, Depends()]):
  user = get_user(form.username)
  if not user or not verify_password(form.password, user["hashed_password"]):
    raise HTTPException(
      status_code=status.HTTP_401_UNAUTHORIZED,
      detail="Incorrect username or password",
      headers={"WWW-Authenticate": "Bearer"},
    )
  return TokenResponse(access_token=create_access_token(form.username))


@router.get("/me", response_model=UserInfo)
async def me(username: Annotated[str, Depends(get_current_username)]):
  return UserInfo(username=username)
