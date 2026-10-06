from datetime import datetime

from pydantic import BaseModel


class LinkCreateData(BaseModel):
    short_code: str
    destination_url: str

    is_custom_alias: bool = False

    expires_at: datetime | None = None
    password_hash: str | None = None
    campaign_name: str | None = None