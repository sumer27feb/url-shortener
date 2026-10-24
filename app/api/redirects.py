from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import RedirectResponse

from app.cache.redis import get_redis
from app.db.session import get_db
from app.services.redirect_service import (
    LinkLookupError,
    LinkNotFoundError,
    LinkUnavailableError,
    resolve_link,
)
from app.services.redirect_service import LinkPasswordError


router = APIRouter(
    tags=["redirects"],
)

http_basic = HTTPBasic(auto_error=False)
@router.get("/{short_code}")
async def redirect_short_code(
    short_code: str,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
    credentials: HTTPBasicCredentials | None = Depends(http_basic),
):
    try:
        password = (
            credentials.password
            if credentials is not None
            else None
        )

        print(
            f"[AUTH API] Short code: {short_code}, "
            f"Credentials received: {credentials is not None}, "
            f"Password present: {password is not None}"
        )
        
        link = await resolve_link(
            short_code=short_code,
            db=db,
            redis=redis,
            password=password,
        )

        return RedirectResponse(
            url=link.destination_url,
            status_code=status.HTTP_307_TEMPORARY_REDIRECT,
        )

    except LinkPasswordError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Password required or incorrect.",
            headers={
                "WWW-Authenticate": 'Basic realm="Short Link"'
            },
        )

    except LinkNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Short link not found.",
        )

    except LinkUnavailableError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Short link is unavailable.",
        )

    except LinkLookupError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Unable to resolve the short link right now.",
        )