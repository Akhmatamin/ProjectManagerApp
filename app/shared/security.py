import jwt
from fastapi.concurrency import run_in_threadpool
from app.shared.config import get_settings
from pwdlib import PasswordHash
from typing import Optional
from datetime import timedelta, datetime, timezone



settings = get_settings()


password_hash = PasswordHash.recommended()


async def get_password_hash(password: str) -> str:
    return await run_in_threadpool(password_hash.hash, password)


async def verify_password(plain_password: str, hashed_password: str) -> bool:
    return await run_in_threadpool(password_hash.verify, plain_password, hashed_password)


async def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_lifetime)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)


async def create_refresh_token(data: dict):
    return await create_access_token(data, expires_delta=timedelta(days=settings.refresh_token_lifetime))

