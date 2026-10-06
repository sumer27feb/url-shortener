from datetime import datetime
from pydantic import BaseModel, HttpUrl

class CreatedLinkRequest(BaseModel):
    destination_url: HttpUrl

    custom_alias: str | None = None
    expires_at: datetime | None = None
    password: str | None = None
    campaign_name: str | None = None

class CreateLinkResponse(BaseModel):
    short_code: str
    destination_url: HttpUrl
    expires_at: datetime | None = None

class ResolvedLinkData(BaseModel):
    short_code: str
    destination_url: str

    expires_at: datetime | None = None
    revoked_at: datetime | None = None
    deleted_at: datetime | None = None

    click_count: int

    password_hash: str | None = None

