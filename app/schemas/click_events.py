from datetime import datetime, timezone
from typing import Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class ClickLinkSnapshot(BaseModel):
    short_code: str
    destination_url: str
    is_custom_alias: bool
    created_at: datetime
    expires_at: datetime | None = None
    campaign_name: str | None = None


class ClickRequestMetadata(BaseModel):
    referrer: str | None = None
    user_agent: str | None = None


class LinkClickedEvent(BaseModel):
    event_id: UUID = Field(default_factory=uuid4)
    event_type: Literal["link.clicked"] = "link.clicked"
    event_version: Literal[1] = 1
    occurred_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    link: ClickLinkSnapshot
    request: ClickRequestMetadata
