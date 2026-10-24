
from datetime import datetime, timezone

from anyio import to_thread
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
from app.services.password_service import verify_password


# ---------- Service Exceptions ----------

class LinkNotFoundError(Exception):
    pass


class LinkLookupError(Exception):
    pass


class LinkUnavailableError(Exception):
    pass


class LinkPasswordError(Exception):
    pass


# ---------- Link State Validation ----------

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


# ---------- Password Verification ----------

async def validate_link_password(
    link: ResolvedLinkData,
    password: str | None,
) -> None:

    # Unprotected links need no password
    if link.password_hash is None:
        return

    if password is None:
        print(f"[AUTH] Password required for '{link.short_code}'")
        raise LinkPasswordError()

    is_valid = await to_thread.run_sync(
        verify_password,
        password,
        link.password_hash,
    )

    if not is_valid:
        print(f"[AUTH] Invalid password for '{link.short_code}'")
        raise LinkPasswordError()

    print(f"[AUTH] Password verified for '{link.short_code}'")


# ---------- Redirect Resolution ----------

async def resolve_link(
    short_code: str,
    db: AsyncSession,
    redis: Redis,
    password: str | None = None,
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
            print(
                f"[DB LOOKUP] Searching PostgreSQL for '{short_code}'"
            )

            link = await get_link_by_short_code(
                db=db,
                short_code=short_code,
            )

        except SQLAlchemyError as exc:
            print(f"[DB ERROR] Failed lookup for '{short_code}'")
            raise LinkLookupError() from exc

        if link is None:
            print(f"[DB MISS] '{short_code}' does not exist")
            raise LinkNotFoundError()

        print(f"[DB HIT] Found '{short_code}' in PostgreSQL")

    # 3. Validate link lifecycle
    validate_link_state(link)

    # 4. Verify password BEFORE counting clicks
    await validate_link_password(
        link=link,
        password=password,
    )

    # 5. Cache metadata on a cache miss
    if cached_link is None:
        await cache_link(
            redis=redis,
            link=link,
        )

    # 6. Count only authorized redirects
    await increment_click_count(
        redis=redis,
        link=link,
    )

    print(f"[REDIRECT] Resolved '{short_code}'")

    return link
