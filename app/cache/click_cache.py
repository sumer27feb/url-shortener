from redis.asyncio import Redis
from redis.exceptions import RedisError

from app.core.config import CLICK_COUNT_PREFIX, CLICK_DIRTY_SET
from app.schemas.links import ResolvedLinkData


def click_count_key(short_code: str) -> str:
    return f"{CLICK_COUNT_PREFIX}{short_code}"


async def increment_click_count(
    redis: Redis,
    short_code: str,
) -> int | None:
    try:
        pending_clicks = await redis.incr(
            click_count_key(short_code)
        )

        print(
            f"[CLICK] '{short_code}' total clicks = "
            f"{pending_clicks}"
        )

        return pending_clicks

    except RedisError as exc:
        print(
            f"[CLICK ERROR] Failed to record click for "
            f"'{short_code}': {exc}"
        )

        return None

# Executed atomically by Redis
INCREMENT_CLICK_SCRIPT = """
-- Initialize counter from persisted PostgreSQL total if absent
redis.call("SET", KEYS[1], ARGV[2], "NX")

-- Mark the link as requiring synchronization
redis.call("SADD", KEYS[2], ARGV[1])

-- Increment and return the new total
return redis.call("INCR", KEYS[1])
"""

async def increment_click_count(
        redis: Redis,
        link: ResolvedLinkData,
) -> int | None:

    try:
        current_count = await redis.eval(
            INCREMENT_CLICK_SCRIPT,
            2,
            click_count_key(link.short_code),
            CLICK_DIRTY_SET,
            link.short_code,
            link.click_count,
        )

        print(
            f"[CLICK] '{link.short_code}' "
            f"total clicks = {current_count}"
        )

        return int(current_count)

    except RedisError as exc:
        print(
            f"[CLICK ERROR] Failed to record click for "
            f"'{link.short_code}': {exc}"
        )
        return None

async def get_total_clicks(
    redis: Redis,
    short_code: str,
) -> int | None:
    try:
        value = await redis.get(
            click_count_key(short_code)
        )

        if value is None:
            return None

        return int(value)

    except (RedisError, ValueError) as exc:
        print(
            f"[CLICK READ ERROR] Failed to read "
            f"click count for '{short_code}': {exc}"
        )
        return None