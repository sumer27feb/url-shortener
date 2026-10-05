from datetime import datetime
from pydantic import BaseModel

class LinkCacheData(BaseModel):
    destination_url: str
    expires_at: datetime | None = None
    revoked_at: datetime | None = None
    deleted_at: datetime | None = None

    max_clicks: int | None = None
    password_protected: bool = False