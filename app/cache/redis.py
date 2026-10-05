from app.core.config import REDIS_URL

from redis.asyncio import Redis

if REDIS_URL is None:
    raise RuntimeError("REDIS_URL is not set")

redis_client = Redis.from_url(
    REDIS_URL,
    encoding="utf-8",
    decode_responses=True,
)

async def get_redis() ->Redis:
    return redis_client

async def close_redis():
    await redis_client.aclose()