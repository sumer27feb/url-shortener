import os

from dotenv import load_dotenv


load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
REDIS_URL = os.getenv("REDIS_URL")
CACHE_PREFIX = "urlshortener:link:"
CACHE_TTL_SECONDS = 300
CLICK_COUNT_PREFIX = "urlshortener:clicks:total:"
CLICK_DIRTY_SET = "urlshortener:clicks:dirty"