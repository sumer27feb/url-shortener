from datetime import date, datetime
from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.click_events import ClickEvent
from app.schemas.click_events import LinkClickedEvent


async def insert_click_event(
    db: AsyncSession,
    event: LinkClickedEvent,
) -> bool:

    stmt = (
        insert(ClickEvent)
        .values(
            event_id=event.event_id,
            short_code=event.link.short_code,
            occurred_at=event.occurred_at,
            event_payload=event.model_dump(mode="json"),
        )
        .on_conflict_do_nothing(
            index_elements=[ClickEvent.event_id]
        )
    )

    result = await db.execute(stmt)

    return result.rowcount == 1

async def count_click_events(
    db: AsyncSession,
    short_code: str,
) -> int:
    stmt = (
        select(func.count())
        .select_from(ClickEvent)
        .where(ClickEvent.short_code == short_code)
    )

    return await db.scalar(stmt) or 0


async def get_daily_click_counts(
    db: AsyncSession,
    short_code: str,
    start: datetime,
    end: datetime,
) -> dict[date, int]:

    # Explicit UTC grouping, independent of DB timezone.
    click_date = func.date(
        func.timezone("UTC", ClickEvent.occurred_at)
    )

    stmt = (
        select(
            click_date.label("click_date"),
            func.count().label("clicks"),
        )
        .where(
            ClickEvent.short_code == short_code,
            ClickEvent.occurred_at >= start,
            ClickEvent.occurred_at < end,
        )
        .group_by(click_date)
        .order_by(click_date)
    )

    result = await db.execute(stmt)

    return {
        row.click_date: row.clicks
        for row in result
    }


async def get_recent_click_events(
    db: AsyncSession,
    short_code: str,
    limit: int = 10,
):
    stmt = (
        select(
            ClickEvent.event_id,
            ClickEvent.occurred_at,
        )
        .where(ClickEvent.short_code == short_code)
        .order_by(
            ClickEvent.occurred_at.desc(),
            ClickEvent.event_id.desc(),
        )
        .limit(limit)
    )

    result = await db.execute(stmt)

    return result.all()
