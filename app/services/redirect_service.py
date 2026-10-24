
from datetime import datetime, timezone

from redis.asyncio import Redis
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.cache.link_cache import (
    cache_link,
    get_cached_link,
)
from app.cache.click_cache import increment_click_count
from app.db.repositories.link_repository import get_link_by_short_code
from app.schemas.links import ResolvedLinkData


class LinkNotFoundError(Exception):
    pass


class LinkLookupError(Exception):
    pass


class LinkUnavailableError(Exception):
    pass


def validate_link_state(link: ResolvedLinkData) -> None:
    if link.deleted_at is not None:
        print(f"[REDIRECT] Link '{link.short_code}' is deleted")
        raise LinkUnavailableError()

    if link.revoked_at is not None:
        print(f"[REDIRECT] Link '{link.short_code}' is revoked")
        raise LinkUnavailableError()

    if (
        link.expires_at is not None
        and link.expires_at <= datetime.now(timezone.utc)
    ):
        print(f"[REDIRECT] Link '{link.short_code}' is expired")
        raise LinkUnavailableError()


async def resolve_link(
    short_code: str,
    db: AsyncSession,
    redis: Redis,
) -> ResolvedLinkData:

    short_code = short_code.lower()
    print(f"[REDIRECT] Resolving short code: {short_code}")

    # 1. Try Redis first
    cached_link = await get_cached_link(
        redis=redis,
        short_code=short_code,
    )

    if cached_link is not None:
        print(f"[CACHE HIT] {short_code}")
        link = cached_link

    else:
        print(f"[CACHE MISS] {short_code}")

        # 2. Redis miss -> PostgreSQL
        try:
            print(f"[DB LOOKUP] Searching PostgreSQL for '{short_code}'")

            link = await get_link_by_short_code(
                db=db,
                short_code=short_code,
            )

        except SQLAlchemyError as exc:
            print(f"[DB ERROR] Failed lookup for '{short_code}'")
            raise LinkLookupError() from exc

        # 3. Short code doesn't exist
        if link is None:
            print(f"[DB MISS] '{short_code}' does not exist")
            raise LinkNotFoundError()

        print(f"[DB HIT] Found '{short_code}' in PostgreSQL")

    # 4. Common validation for both paths
    validate_link_state(link)

    # 5. Cache only if resolved from PostgreSQL
    if cached_link is None:
        await cache_link(
            redis=redis,
            link=link,
        )
        print(f"[CACHE SET] Cached '{short_code}'")

    # 6. Increment total clicks and mark dirty in Redis
    await increment_click_count(
        redis=redis,
        link=link,
    )

    print(f"[REDIRECT] Resolved '{short_code}'")

    return link