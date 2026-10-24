import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
REDIS_URL = os.getenv("REDIS_URL")

# Link caching
CACHE_PREFIX = os.getenv("CACHE_PREFIX", "urlshortener:link:")
CACHE_TTL_SECONDS = int(os.getenv("CACHE_TTL_SECONDS", "300"))

# Click analytics
CLICK_COUNT_PREFIX = os.getenv(
    "CLICK_COUNT_PREFIX",
    "urlshortener:clicks:total:"
)

CLICK_DIRTY_SET = os.getenv(
    "CLICK_DIRTY_SET",
    "urlshortener:clicks:dirty"
)

# Click flush worker
CLICK_FLUSH_INTERVAL_SECONDS = int(
    os.getenv("CLICK_FLUSH_INTERVAL_SECONDS", "60")
)

CLICK_FLUSH_BATCH_SIZE = int(
    os.getenv("CLICK_FLUSH_BATCH_SIZE", "100")
)