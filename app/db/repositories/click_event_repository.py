
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
