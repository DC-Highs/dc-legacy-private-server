"""Dragon level rules."""
from typing import Any, Optional

MAX_DRAGON_LEVEL = 40


def level_from_xp(xp: Optional[int], dragon_type: Any = None) -> int:
    if not xp or xp <= 0:
        return 1

    calculated_level = (xp // 4) + 1

    if calculated_level > MAX_DRAGON_LEVEL:
        calculated_level = MAX_DRAGON_LEVEL

    return int(calculated_level)
