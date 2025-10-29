import json
import os
from typing import Any, Optional

import redis.asyncio as aioredis

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

redis_client: Optional[aioredis.Redis] = None


async def get_redis() -> aioredis.Redis:
    """Get Redis client instance"""
    global redis_client
    if redis_client is None:
        redis_client = await aioredis.from_url(REDIS_URL, decode_responses=True)
    return redis_client


async def close_redis() -> None:
    """Close Redis connection"""
    global redis_client
    if redis_client:
        await redis_client.close()
        redis_client = None


async def get_cached(key: str) -> Optional[Any]:
    """
    Get cached value from Redis
    Returns None if key doesn't exist
    """
    client = await get_redis()
    value = await client.get(key)
    if value:
        return json.loads(value)
    return None


async def set_cached(key: str, value: Any, expire: int = 3600) -> None:
    """
    Set cached value in Redis with expiration time in seconds
    Default expiration: 1 hour
    """
    client = await get_redis()
    await client.setex(key, expire, json.dumps(value))


async def delete_cached(key: str) -> None:
    """Delete cached value from Redis"""
    client = await get_redis()
    await client.delete(key)


async def clear_pattern(pattern: str) -> None:
    """Delete all keys matching pattern"""
    client = await get_redis()
    async for key in client.scan_iter(match=pattern):
        await client.delete(key)
