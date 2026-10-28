
import time
from dataclasses import dataclass

from redis.asyncio import Redis


RATE_LIMIT_SCRIPT = """
local key = KEYS[1]
local limit = tonumber(ARGV[1])
local expiry = tonumber(ARGV[2])

local current = tonumber(redis.call("GET", key) or "0")

-- Reject without incrementing an exhausted quota.
if current >= limit then
    return {0, 0, redis.call("TTL", key)}
end

-- Reserve a request slot.
current = redis.call("INCR", key)

-- Only the first request sets the window expiration.
if current == 1 then
    redis.call("EXPIRE", key, expiry)
end

return {
    1,
    limit - current,
    redis.call("TTL", key)
}
"""


@dataclass(frozen=True)
class RateLimitDecision:
    allowed: bool
    remaining: int
    retry_after: int


async def check_rate_limit(
    redis: Redis,
    *,
    scope: str,
    identifier: str,
    limit: int,
    window_seconds: int,
) -> RateLimitDecision:

    if limit <= 0 or window_seconds <= 0:
        raise ValueError("Rate limit and window must be positive")

    now = int(time.time())

    window_id = now // window_seconds
    expiry = window_seconds - (now % window_seconds)

    key = (
        f"urlshortener:ratelimit:"
        f"{scope}:{identifier}:{window_id}"
    )

    result = await redis.eval(
        RATE_LIMIT_SCRIPT,
        1,
        key,
        limit,
        expiry,
    )

    return RateLimitDecision(
        allowed=bool(result[0]),
        remaining=int(result[1]),
        retry_after=max(1, int(result[2])),
    )
