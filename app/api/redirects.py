from fastapi import APIRouter
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import RedirectResponse

from app.cache.redis import get_redis
from app.db.session import get_db
from app.services.redirect_service import (
    LinkNotFoundError,
    resolve_short_code,
)

router = APIRouter(tags=["redirects"])

@router.get("/health")
def health():
    return {"message": "redirects API is healthy"}