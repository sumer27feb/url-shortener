from fastapi import APIRouter, HTTPException, status, Depends

from app.schemas.links import CreateLinkResponse, CreatedLinkRequest
from app.services.link_service import (
    create_link as create_link_service,
    InvalidCustomAliasError,
    CustomAliasConflictError,
    ShortCodeGenerationError,
    LinkPersistenceError,
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

@router.get("/db-test")
async def db_test(
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(text("SELECT 1"))

    return {
        "database": "connected",
        "result": result.scalar(),
    }