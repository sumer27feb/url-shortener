from app.core.constants import RESERVED_SHORT_CODES
from app.db.models.links import Link
from app.db.repositories.link_repository import create_link as create_link_db
from app.schemas.link_internal import LinkCreateData
from app.schemas.links import CreatedLinkRequest
from app.services.short_code_service import generate_short_code

from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession


MAX_SHORT_CODE_RETRIES = 5
SHORT_CODE_UNIQUE_CONSTRAINT = "links_short_code_key"


# ---------- Service/domain errors ----------

class LinkServiceError(Exception):
    """Base error for link creation failures."""
    pass


class InvalidCustomAliasError(LinkServiceError):
    pass


class CustomAliasConflictError(LinkServiceError):
    pass


class ShortCodeGenerationError(LinkServiceError):
    pass


class LinkPersistenceError(LinkServiceError):
    pass


# ---------- Validation ----------

def validate_custom_alias(short_code: str):
    if short_code.lower() in RESERVED_SHORT_CODES:
        raise InvalidCustomAliasError(
            "This short code is reserved"
        )


# ---------- Helpers ----------

def build_link_data(
    payload: CreatedLinkRequest,
    short_code: str,
    is_custom_alias: bool,
) -> LinkCreateData:
    return LinkCreateData(
        short_code=short_code,
        destination_url=str(payload.destination_url),
        is_custom_alias=is_custom_alias,
        expires_at=payload.expires_at,
        max_clicks=payload.max_clicks,

        # temporary for testing
        password_hash=payload.password
        if payload.password
        else None,

        campaign_name=payload.campaign_name,
    )


def is_short_code_collision(exc: IntegrityError) -> bool:
    original_error = exc.orig

    sqlstate = getattr(original_error, "sqlstate", None)

    constraint_name = getattr(
        getattr(original_error, "diag", None),
        "constraint_name",
        None,
    )

    return (
        sqlstate == "23505"
        and constraint_name == SHORT_CODE_UNIQUE_CONSTRAINT
    )


# ---------- Creation workflow ----------

async def create_link(
    payload: CreatedLinkRequest,
    db: AsyncSession,
) -> Link:

    # ---------------------------------
    # Custom alias flow
    # ---------------------------------

    if payload.custom_alias:
        validate_custom_alias(payload.custom_alias)

        short_code = payload.custom_alias.lower()

        link_data = build_link_data(
            payload=payload,
            short_code=short_code,
            is_custom_alias=True,
        )

        try:
            link = await create_link_db(
                db=db,
                data=link_data,
            )

            await db.commit()

            return link

        except IntegrityError as exc:
            await db.rollback()

            if is_short_code_collision(exc):
                raise CustomAliasConflictError() from exc

            raise LinkPersistenceError() from exc

        except SQLAlchemyError as exc:
            await db.rollback()

            raise LinkPersistenceError() from exc


    # ---------------------------------
    # Generated short-code flow
    # ---------------------------------

    for _ in range(MAX_SHORT_CODE_RETRIES):

        short_code = generate_short_code()

        link_data = build_link_data(
            payload=payload,
            short_code=short_code,
            is_custom_alias=False,
        )

        try:
            link = await create_link_db(
                db=db,
                data=link_data,
            )

            await db.commit()

            return link

        except IntegrityError as exc:
            await db.rollback()

            # Expected generated-code collision:
            # generate a new code and try again.
            if is_short_code_collision(exc):
                continue

            # Some OTHER DB integrity constraint failed.
            raise LinkPersistenceError() from exc

        except SQLAlchemyError as exc:
            await db.rollback()

            raise LinkPersistenceError() from exc


    raise ShortCodeGenerationError()