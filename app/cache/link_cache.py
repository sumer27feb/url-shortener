from redis.asyncio import Redis
from redis.exceptions import RedisError

from app.schemas.link_cache import LinkCacheData
from app.core.config import CACHE_PREFIX, CACHE_TTL_SECONDS

def cache_key(short_code: str) -> str:
    return f"{CACHE_PREFIX}{short_code}"

async def get_cached_link(
        redis: Redis,
        short_code: str
) -> LinkCacheData | None:
    try:
        value = await redis.get(
            cache_key(short_code)
        )

        if value is None:
            return None

        return LinkCacheData.model_validate_json(value)

    except RedisError:
        return None

async def cache_link(
        redis: Redis,
        short_code: str,
        data: LinkCacheData,
):
    try:
        await redis.set(
            cache_key(short_code),
            data.model_dump_json(),
            ex=CACHE_TTL_SECONDS,
        )

    except RedisError:
        pass