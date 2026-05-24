from datetime import datetime, timedelta, timezone
from uuid import uuid4

import redis.asyncio as redis
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models.user import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security_scheme = HTTPBearer()

REFRESH_TOKEN_EXPIRE = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
ACCESS_TOKEN_EXPIRE = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)


def _load_private_key() -> str:
    if settings.JWT_PRIVATE_KEY_PATH:
        return open(settings.JWT_PRIVATE_KEY_PATH).read()
    return settings.SECRET_KEY


def _load_public_key() -> str:
    if settings.JWT_PUBLIC_KEY_PATH:
        return open(settings.JWT_PUBLIC_KEY_PATH).read()
    return settings.SECRET_KEY


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, hash: str) -> bool:
    return pwd_context.verify(password, hash)


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + ACCESS_TOKEN_EXPIRE
    to_encode.update({"exp": expire, "type": "access", "jti": str(uuid4())})
    return jwt.encode(to_encode, _load_private_key(), algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(data: dict) -> tuple[str, str]:
    jti = str(uuid4())
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + REFRESH_TOKEN_EXPIRE
    to_encode.update({"exp": expire, "type": "refresh", "jti": jti})
    token = jwt.encode(to_encode, _load_private_key(), algorithm=settings.JWT_ALGORITHM)
    return token, jti


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, _load_public_key(), algorithms=[settings.JWT_ALGORITHM])
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")


async def get_redis() -> redis.Redis:
    return redis.from_url(settings.REDIS_URL, decode_responses=True)


async def _is_token_blacklisted(jti: str) -> bool:
    r = await get_redis()
    result = await r.get(f"bl:{jti}")
    await r.close()
    return bool(result)


async def blacklist_token(jti: str, ttl: int) -> None:
    r = await get_redis()
    await r.setex(f"bl:{jti}", ttl, "1")
    await r.close()


async def store_refresh_token_family(jti: str, user_id: str, ttl: int) -> None:
    r = await get_redis()
    await r.setex(f"rt:{user_id}:{jti}", ttl, "1")
    await r.close()


async def invalidate_refresh_family(user_id: str, jti: str) -> None:
    r = await get_redis()
    pattern = f"rt:{user_id}:*"
    cursor = 0
    while True:
        cursor, keys = await r.scan(cursor, match=pattern, count=100)
        for key in keys:
            key_jti = key.split(":")[-1]
            if key_jti != jti:
                await r.delete(key)
        if cursor == 0:
            break
    await r.close()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    payload = decode_token(credentials.credentials)
    jti = payload.get("jti")
    if jti and await _is_token_blacklisted(jti):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has been revoked")

    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user
