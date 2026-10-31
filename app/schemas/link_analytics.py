
from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field


class DailyClickCount(BaseModel):
    date: date
    clicks: int = Field(ge=0)


class RecentClick(BaseModel):
    event_id: UUID
    occurred_at: datetime


class LinkAnalyticsResponse(BaseModel):
    short_code: str
    recorded_events_total: int = Field(ge=0)
    period_days: int = Field(ge=1)
    daily_clicks: list[DailyClickCount]
    recent_clicks: list[RecentClick]
