
import asyncio
import sys
from getpass import getpass

from app.db.session import AsyncLocalSession
from app.db.repositories.link_repository import get_link_by_short_code
from app.services.password_service import verify_password


async def main():
    password = getpass("Enter the link password: ")

    async with AsyncLocalSession() as db:
        link = await get_link_by_short_code(
            db=db,
            short_code="protectedtest2",
        )

        if link is None:
            print("Link not found")
            return

        if link.password_hash is None:
            print("Link is not password protected")
            return

        is_valid = verify_password(
            password,
            link.password_hash,
        )

        print(f"Password matches stored hash: {is_valid}")


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(
            asyncio.WindowsSelectorEventLoopPolicy()
        )

    asyncio.run(main())
