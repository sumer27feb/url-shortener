from collections import Counter

from app.core.constants import SHORT_CODE_ALPHABET, SHORT_CODE_LENGTH
from app.services.short_code_service import generate_short_code


SAMPLE_SIZE = 1_000_000


def test_short_code_generation():
    codes = [generate_short_code() for _ in range(SAMPLE_SIZE)]

    # 1. Every code must have the correct length
    assert all(len(code) == SHORT_CODE_LENGTH for code in codes)

    # 2. Every character must belong to our allowed alphabet
    assert all(
        char in SHORT_CODE_ALPHABET
        for code in codes
        for char in code
    )

    # 3. Count duplicates
    unique_codes = set(codes)
    duplicate_count = SAMPLE_SIZE - len(unique_codes)

    # 4. Inspect character distribution
    character_counts = Counter(
        char
        for code in codes
        for char in code
    )

    total_characters = SAMPLE_SIZE * SHORT_CODE_LENGTH

    print(f"Generated codes: {SAMPLE_SIZE:,}")
    print(f"Unique codes:    {len(unique_codes):,}")
    print(f"Duplicates:      {duplicate_count:,}")
    print()

    print("Character distribution:")
    for char in SHORT_CODE_ALPHABET:
        count = character_counts[char]
        percentage = count / total_characters * 100

        print(
            f"{char}: {count:>6,} "
            f"({percentage:.3f}%)"
        )


if __name__ == "__main__":
    test_short_code_generation()