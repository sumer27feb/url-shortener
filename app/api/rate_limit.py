
import logging

from fastapi import Depends, HTTPException, Request, status
from redis.asyncio import Redis
from redis.exceptions import RedisError

from app.cache.redis import get_redis
from app.services.rate_limit_service import check_rate_limit


logger = logging.getLogger(__name__)

CREATE_LIMIT = 10
CREATE_WINDOW_SECONDS = 60


async def enforce_create_rate_limit(
    request: Request,
    redis: Redis = Depends(get_redis),
) -> None:

    if request.client is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Client identity unavailable.",
        )

    client_ip = request.client.host

    try:
        decision = await check_rate_limit(
            redis=redis,
            scope="links_create",
            identifier=client_ip,
            limit=CREATE_LIMIT,
            window_seconds=CREATE_WINDOW_SECONDS,
        )

    except RedisError:
        logger.exception(
            "Redis unavailable during rate-limit check"
        )
        # Fail-open: preserve link creation availability.
        return

    if not decision.allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many link creation requests.",
            headers={
                "Retry-After": str(decision.retry_after),
            },
        )
