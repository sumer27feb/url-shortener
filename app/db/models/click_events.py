
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import DateTime, Index, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ClickEvent(Base):
    __tablename__ = "click_events"

    __table_args__ = (
        Index(
            "ix_click_events_short_code_occurred_at",
            "short_code",
            "occurred_at",
        ),
    )

    event_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
    )

    short_code: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    event_payload: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
    )
