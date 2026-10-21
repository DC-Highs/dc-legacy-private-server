"""Dragonarium helpers."""
from typing import Any, Dict, Iterable

from dragon_city.enums import DragonAttribute as Attr
from dragon_city.enums import DragonariumTab

DEFAULT_SLOTS = [2, 2, 2, 1, 1]
TAB_COUNT = 5


def tab_for_attributes(attributes: Iterable[str]) -> DragonariumTab:
    """Pick the dragonarium tab for a dragon from its attribute codes."""
    attributes = list(attributes)

    if Attr.PURE in attributes:
        return DragonariumTab.PURE
    if Attr.LEGENDARY in attributes:
        return DragonariumTab.LEGENDARY
    if Attr.DARK in attributes:
        return DragonariumTab.DARK
    if Attr.METAL in attributes:
        return DragonariumTab.METAL
    return DragonariumTab.ELEMENTAL


def ensure_slots(private_state: Dict[str, Any]) -> list:
    if "dragonariumSlot" not in private_state or len(private_state.get("dragonariumSlot", [])) < TAB_COUNT:
        private_state["dragonariumSlot"] = list(DEFAULT_SLOTS)
    return private_state["dragonariumSlot"]
