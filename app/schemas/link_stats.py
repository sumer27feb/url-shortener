from pydantic import BaseModel, Field


class LinkStatsResponse(BaseModel):
    short_code: str
    total_clicks: int = Field(ge=0)
