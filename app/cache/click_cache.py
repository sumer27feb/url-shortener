from redis.asyncio import Redis
from redis.exceptions import RedisError

from app.core.config import CLICK_COUNT_PREFIX


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