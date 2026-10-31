
from datetime import datetime, time, timedelta, timezone

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repositories.link_repository import (
    get_link_by_short_code,
)
from app.db.repositories.click_event_repository import (
    count_click_events,
    get_daily_click_counts,
    get_recent_click_events,
)
from app.schemas.link_analytics import (
    DailyClickCount,
    RecentClick,
    LinkAnalyticsResponse,
)


class LinkAnalyticsNotFoundError(Exception):
    pass


class LinkAnalyticsLookupError(Exception):
    pass


async def get_link_analytics(
    short_code: str,
    days: int,
    db: AsyncSession,
) -> LinkAnalyticsResponse:

    short_code = short_code.lower()

    try:
        link = await get_link_by_short_code(
            db=db,
            short_code=short_code,
        )

        if link is None:
            raise LinkAnalyticsNotFoundError()

        today = datetime.now(timezone.utc).date()
        first_day = today - timedelta(days=days - 1)

        start = datetime.combine(
            first_day,
            time.min,
            tzinfo=timezone.utc,
        )

        end = datetime.combine(
            today + timedelta(days=1),
            time.min,
            tzinfo=timezone.utc,
        )

        total = await count_click_events(
            db=db,
            short_code=short_code,
        )

        daily_counts = await get_daily_click_counts(
            db=db,
            short_code=short_code,
            start=start,
            end=end,
        )

        recent_events = await get_recent_click_events(
            db=db,
            short_code=short_code,
        )

    except SQLAlchemyError as exc:
        raise LinkAnalyticsLookupError() from exc

    daily_clicks = [
        DailyClickCount(
            date=first_day + timedelta(days=i),
            clicks=daily_counts.get(
                first_day + timedelta(days=i),
                0,
            ),
        )
        for i in range(days)
    ]

    recent_clicks = [
        RecentClick(
            event_id=row.event_id,
            occurred_at=row.occurred_at,
        )
        for row in recent_events
    ]

    return LinkAnalyticsResponse(
        short_code=short_code,
        recorded_events_total=total,
        period_days=days,
        daily_clicks=daily_clicks,
        recent_clicks=recent_clicks,
    )
