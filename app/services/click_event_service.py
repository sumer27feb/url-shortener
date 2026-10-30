from app.schemas.links import ResolvedLinkData
from app.schemas.click_events import (
    ClickLinkSnapshot,
    ClickRequestMetadata,
    LinkClickedEvent,
)


def build_click_event(
    link: ResolvedLinkData,
    *,
    referrer: str | None,
    user_agent: str | None,
) -> LinkClickedEvent:

    return LinkClickedEvent(
        link=ClickLinkSnapshot(
            short_code=link.short_code,
            destination_url=link.destination_url,
            is_custom_alias=link.is_custom_alias,
            created_at=link.created_at,
            expires_at=link.expires_at,
            campaign_name=link.campaign_name,
        ),
        request=ClickRequestMetadata(
            referrer=referrer,
            user_agent=user_agent,
        ),
    )
