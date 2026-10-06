from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.links import Link
from app.schemas.link_internal import LinkCreateData
from app.schemas.links import ResolvedLinkData

async def create_link(
    db: AsyncSession,
    data: LinkCreateData,
) -> Link:
    link = Link(**data.model_dump())

    db.add(link)
    await db.flush()

    return link

async def get_link_by_short_code(
        db: AsyncSession,
        short_code: str,
) -> ResolvedLinkData | None:
    result = await db.execute(
        select(Link).where(
            Link.short_code == short_code
        )
    )

    link = result.scalar_one_or_none()

    if link is None:
        return None

    return ResolvedLinkData(
        short_code=link.short_code,
        destination_url=link.destination_url,
        expires_at=link.expires_at,
        revoked_at=link.revoked_at,
        deleted_at=link.deleted_at,
        click_count=link.click_count,
        password_hash=link.password_hash,
    )

async def update_click_count(
        db:AsyncSession,
        short_code: str,
        click_count: int,
) -> None:
    await db.execute(
        update(Link)
        .where(Link.short_code == short_code)
        .values(
            click_count=func.greatest(
                Link.click_count,
                click_count,
            )
        )
    )