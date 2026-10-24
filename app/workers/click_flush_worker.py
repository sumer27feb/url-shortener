import asyncio
import sys

from redis.asyncio import Redis

from app.core.config import (
    REDIS_URL,
    CLICK_FLUSH_INTERVAL_SECONDS,
    CLICK_FLUSH_BATCH_SIZE,
)
from app.db.session import get_db
from app.services.click_flush_service import flush_click_counts


# Required for async Psycopg on Windows
if sys.platform == "win32":
    asyncio.set_event_loop_policy(
        asyncio.WindowsSelectorEventLoopPolicy()
    )


MAX_BATCHES_PER_CYCLE = 10


async def run_flush_cycle(redis: Redis) -> int:
    total_flushed = 0

    for _ in range(MAX_BATCHES_PER_CYCLE):

        # Reuse our existing async database session dependency
        async for db in get_db():
            flushed = await flush_click_counts(
                redis=redis,
                db=db,
                batch_size=CLICK_FLUSH_BATCH_SIZE,
            )

        total_flushed += flushed

        # Stop if fewer than a full batch were acknowledged.
        # Remaining dirty links, if any, retry next cycle.
        if flushed < CLICK_FLUSH_BATCH_SIZE:
            break

    return total_flushed


async def run_worker() -> None:

    if not REDIS_URL:
        raise RuntimeError("REDIS_URL is not configured")

    redis = Redis.from_url(
        REDIS_URL,
        encoding="utf-8",
        decode_responses=True,
    )

    print("[WORKER] Click flush worker started")
    print(
        f"[WORKER] Flush interval: "
        f"{CLICK_FLUSH_INTERVAL_SECONDS}s"
    )

    try:
        while True:
            try:
                print("[WORKER] Starting flush cycle")

                flushed = await run_flush_cycle(redis)

                print(
                    f"[WORKER] Cycle completed. "
                    f"Cleaned entries: {flushed}"
                )

            except Exception as exc:
                print(f"[WORKER ERROR] {exc}")

            await asyncio.sleep(
                CLICK_FLUSH_INTERVAL_SECONDS
            )

    finally:
        await redis.aclose()
        print("[WORKER] Redis connection closed")


if __name__ == "__main__":
    try:
        asyncio.run(run_worker())
    except KeyboardInterrupt:
        print("[WORKER] Stopped")
