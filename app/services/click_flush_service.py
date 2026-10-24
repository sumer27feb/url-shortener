
from redis.asyncio import Redis
from redis.exceptions import RedisError
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.cache.click_cache import click_count_key
from app.core.config import (
    CLICK_DIRTY_SET,
    CLICK_FLUSH_BATCH_SIZE,
)
from app.db.repositories.link_repository import update_click_count


# Atomically remove a dirty entry only when its
# Redis total still matches the persisted total.
ACK_FLUSH_SCRIPT = """
local current_total = redis.call("GET", KEYS[1])

if current_total == ARGV[1] then
    return redis.call("SREM", KEYS[2], ARGV[2])
end

return 0
"""


async def flush_click_counts(
    redis: Redis,
    db: AsyncSession,
    batch_size: int = CLICK_FLUSH_BATCH_SIZE,
) -> int:

    # 1. Select dirty links without removing them.
    try:
        short_codes = await redis.srandmember(
            CLICK_DIRTY_SET,
            number=batch_size,
        )
    except RedisError as exc:
        print(f"[FLUSH ERROR] Failed to read dirty set: {exc}")
        return 0

    if not short_codes:
        print("[FLUSH] No dirty links found")
        return 0

    flushed = 0

    for short_code in short_codes:

        # 2. Read the current Redis click total.
        try:
            value = await redis.get(
                click_count_key(short_code)
            )

            if value is None:
                print(
                    f"[FLUSH WARNING] Missing counter "
                    f"for '{short_code}'"
                )
                continue

            redis_total = int(value)

        except (RedisError, ValueError) as exc:
            print(
                f"[FLUSH ERROR] Failed to read "
                f"'{short_code}': {exc}"
            )
            continue

        # 3. Persist the absolute total to PostgreSQL.
        try:
            await update_click_count(
                db=db,
                short_code=short_code,
                click_count=redis_total,
            )

            await db.commit()

        except SQLAlchemyError as exc:
            await db.rollback()

            print(
                f"[FLUSH ERROR] PostgreSQL update failed "
                f"for '{short_code}': {exc}"
            )
            continue

        # 4. Acknowledge only if no new clicks arrived.
        try:
            removed = await redis.eval(
                ACK_FLUSH_SCRIPT,
                2,
                click_count_key(short_code),
                CLICK_DIRTY_SET,
                str(redis_total),
                short_code,
            )

            if removed == 1:
                flushed += 1
                print(
                    f"[FLUSH SUCCESS] '{short_code}' "
                    f"persisted={redis_total}, marked clean"
                )
            else:
                print(
                    f"[FLUSH PENDING] '{short_code}' "
                    f"received newer clicks or was "
                    f"already acknowledged"
                )

        except RedisError as exc:
            print(
                f"[FLUSH ERROR] Could not acknowledge "
                f"'{short_code}': {exc}"
            )

    return flushed
