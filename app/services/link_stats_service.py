from redis.asyncio import Redis
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.cache.click_cache import get_total_clicks
from app.db.repositories.link_repository import get_link_by_short_code


class LinkStatsNotFoundError(Exception):
    pass


class LinkStatsLookupError(Exception):
    pass


async def get_link_stats(
    short_code: str,
    db: AsyncSession,
    redis: Redis,
) -> int:

    short_code = short_code.lower()

    # 1. Read persisted count from PostgreSQL
    try:
        link = await get_link_by_short_code(
            db=db,
            short_code=short_code,
        )

    except SQLAlchemyError as exc:
        print(
            f"[STATS ERROR] PostgreSQL lookup failed "
            f"for '{short_code}': {exc}"
        )
        raise LinkStatsLookupError() from exc

    if link is None:
        raise LinkStatsNotFoundError()

    persisted_count = link.click_count

    # 2. Read the live total from Redis
    redis_count = await get_total_clicks(
        redis=redis,
        short_code=short_code,
    )

    # 3. Redis unavailable or counter missing
    if redis_count is None:
        print(
            f"[STATS] Redis unavailable/missing. "
            f"Using PostgreSQL count: {persisted_count}"
        )
        return persisted_count

    # 4. Return the greatest available total
    total_clicks = max(persisted_count, redis_count)

    print(
        f"[STATS] '{short_code}' "
        f"PostgreSQL={persisted_count}, "
        f"Redis={redis_count}, "
        f"Total={total_clicks}"
    )

    return total_clicks
