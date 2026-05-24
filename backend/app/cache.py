import json
from typing import Any, Optional

import redis.asyncio as redis

from app.config import settings


async def get_redis() -> redis.Redis:
    return redis.from_url(settings.REDIS_URL, decode_responses=True)


async def cache_get(key: str) -> Optional[Any]:
    r = await get_redis()
    value = await r.get(f"cache:{key}")
    await r.close()
    if value:
        return json.loads(value)
    return None


async def cache_set(key: str, value: Any, ttl: int = 300) -> None:
    r = await get_redis()
    await r.setex(f"cache:{key}", ttl, json.dumps(value, default=str))
    await r.close()


async def cache_invalidate(pattern: str = "*") -> None:
    r = await get_redis()
    cursor = 0
    while True:
        cursor, keys = await r.scan(cursor, match=f"cache:{pattern}", count=100)
        if keys:
            await r.delete(*keys)
        if cursor == 0:
            break
    await r.close()
