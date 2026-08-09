import uuid
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.concurrency import run_in_threadpool
from app.shared.db.database import get_db_session
from app.users.models import User
from app.shared.config import (SECRET_KEY, ALGORITHM, REFRESH_TOKEN_LIFETIME, ACCESS_TOKEN_LIFETIME)
from sqlalchemy.ext.asyncio import AsyncSession
from jwt.exceptions import InvalidTokenError
from fastapi.security import OAuth2PasswordBearer
from pwdlib import PasswordHash
from typing import Optional
from datetime import timedelta, datetime, timezone
from sqlalchemy import select

password_hash = PasswordHash.recommended()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

async def get_password_hash(password: str) -> str:
    return await run_in_threadpool(password_hash.hash, password)


async def verify_password(plain_password: str, hashed_password: str) -> bool:
    return await run_in_threadpool(password_hash.verify, plain_password, hashed_password)


async def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_LIFETIME)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


async def create_refresh_token(data: dict):
    return await create_access_token(data, expires_delta=timedelta(days=REFRESH_TOKEN_LIFETIME))


async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db_session)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except InvalidTokenError:
        raise credentials_exception

    stmt = select(User).where(User.id == uuid.UUID(user_id))
    user = await db.scalar(stmt)
    if user is None:
        raise credentials_exception
    return user