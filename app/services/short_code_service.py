import secrets

from app.core.constants import SHORT_CODE_LENGTH, SHORT_CODE_ALPHABET

def generate_short_code() -> str:
    return "".join(
        secrets.choice(SHORT_CODE_ALPHABET)
        for _ in range(SHORT_CODE_LENGTH)
    )
