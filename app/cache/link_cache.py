from pydantic import ValidationError
from redis.asyncio import Redis
from redis.exceptions import RedisError

from app.core.config import CACHE_PREFIX, CACHE_TTL_SECONDS
from app.schemas.links import ResolvedLinkData


def cache_key(short_code: str) -> str:
    return f"{CACHE_PREFIX}{short_code}"


async def get_cached_link(
    redis: Redis,
    short_code: str,
) -> ResolvedLinkData | None:
    try:
        value = await redis.get(
            cache_key(short_code)
        )

        if value is None:
            return None

        return ResolvedLinkData.model_validate_json(value)

    except RedisError as exc:
        print(
            f"[CACHE ERROR] Redis lookup failed for "
            f"'{short_code}': {exc}"
        )
        return None

    except ValidationError as exc:
        print(
            f"[CACHE ERROR] Invalid cached data for "
            f"'{short_code}': {exc}"
        )
        return None


async def cache_link(
    redis: Redis,
    link: ResolvedLinkData,
) -> None:
    try:
        await redis.set(
            cache_key(link.short_code),
            link.model_dump_json(),
            ex=CACHE_TTL_SECONDS,
        )

    except RedisError as exc:
        print(
            f"[CACHE ERROR] Failed to cache "
            f"'{link.short_code}': {exc}"
        )