from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    Identity,
    Text,
    false,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

class Link(Base):
    __tablename__ = "links"

    __table_args__ = (
        CheckConstraint(
            "short_code = lower(short_code)",
            name="ck_links_short_code_lowercase",
        ),
        CheckConstraint(
            "click_count >= 0",
            name="ck_links_click_count_nonnegative",
        ),
        CheckConstraint(
            "max_clicks IS NULL OR max_clicks >= 0",
            name="ck_links_max_clicks_nonnegative",
        ),
    )

    id: Mapped[int] = mapped_column(
        BigInteger,
        Identity(),
        primary_key=True,
    )

    short_code: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        unique=True,
    )

    destination_url: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    is_custom_alias: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=false(),
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    click_count: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        default=0,
        server_default="0",
    )

    max_clicks: Mapped[int | None] = mapped_column(
        BigInteger,
        nullable=True,
    )

    password_hash: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    campaign_name: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )