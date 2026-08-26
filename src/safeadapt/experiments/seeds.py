"""Default experiment seeds."""

DEFAULT_SEEDS = [42, 43, 44]


def parse_seeds(raw: list[int] | None) -> list[int]:
    """Return seed list or defaults."""
    if not raw:
        return list(DEFAULT_SEEDS)
    return list(raw)
