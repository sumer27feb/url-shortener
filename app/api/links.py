from fastapi import APIRouter, HTTPException, status, Depends
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.links import CreateLinkResponse, CreatedLinkRequest
from app.schemas.link_stats import LinkStatsResponse
from app.cache.redis import get_redis
from app.db.session import get_db
from app.services.link_service import (
    create_link as create_link_service,
    InvalidCustomAliasError,
    CustomAliasConflictError,
    ShortCodeGenerationError,
    LinkPersistenceError,
)
from app.services.link_stats_service import (
    LinkStatsNotFoundError,
    LinkStatsLookupError,
    get_link_stats,
)

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db

router = APIRouter(prefix="/links", tags=["links"])

@router.get("/health")
def health():
    return {"message": "links API is healthy"}

@router.post("/create", response_model=CreateLinkResponse,
             status_code=status.HTTP_201_CREATED)
async def create_link(
    payload: CreatedLinkRequest,
    db: AsyncSession = Depends(get_db),
):
    try:
        link = await create_link_service(
            payload=payload,
            db=db,
        )

        return CreateLinkResponse.model_validate({
            "short_code": link.short_code,
            "destination_url": link.destination_url,
            "expires_at": link.expires_at,
        })

    except InvalidCustomAliasError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="That custom alias cannot be used.",
        )

    except CustomAliasConflictError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="That custom alias is already taken.",
        )

    except ShortCodeGenerationError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Could not create the short link right now. Please try again.",
        )

    except LinkPersistenceError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Could not create the short link right now. Please try again.",
        )


@router.get(
    "/{short_code}/stats",
    response_model=LinkStatsResponse,
)
async def read_link_stats(
    short_code: str,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> LinkStatsResponse:

    try:
        total_clicks = await get_link_stats(
            short_code=short_code,
            db=db,
            redis=redis,
        )

    except LinkStatsNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Short link not found.",
        )

    except LinkStatsLookupError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Unable to retrieve link statistics right now.",
        )

    return LinkStatsResponse(
        short_code=short_code.lower(),
        total_clicks=total_clicks,
    )


@router.get("/db-test")
async def db_test(
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(text("SELECT 1"))

    return {
        "database": "connected",
        "result": result.scalar(),
    }