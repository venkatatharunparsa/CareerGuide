from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")


def verify_password(plain_password: str, hashed_password: str) -> bool:
  return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
  return pwd_context.hash(password)


def create_access_token(subject: str) -> str:
  expire = datetime.now(timezone.utc) + timedelta(
    minutes=settings.access_token_expire_minutes
  )
  payload = {"sub": subject, "exp": expire}
  return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


async def get_current_username(
  token: Annotated[str, Depends(oauth2_scheme)],
) -> str:
  credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
  )
  try:
    payload = jwt.decode(
      token, settings.secret_key, algorithms=[settings.algorithm]
    )
    username: str | None = payload.get("sub")
  except JWTError as exc:
    raise credentials_exception from exc

  if username is None:
    raise credentials_exception

  from app.database import get_user

  if not get_user(username):
    raise HTTPException(status_code=404, detail="User not found")
  return username
