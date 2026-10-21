"""Helpers for the player's storage, gifts and owned-dragon book."""
import logging
from typing import Any, Dict, Optional, Tuple

logger = logging.getLogger(__name__)

# (min xp, ownedDragons entry) - checked from the highest threshold down.
_OWNED_DRAGON_STAGES = (
    (24, [1, 2, 3]),
    (12, [1, 2, 0]),
)


def _find_gifts_node(player_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    if "gifts" in player_data:
        return player_data["gifts"]
    if "privateState" in player_data and "gifts" in player_data["privateState"]:
        return player_data["privateState"]["gifts"]
    if "map" in player_data and "gifts" in player_data["map"]:
        return player_data["map"]["gifts"]
    return None


def _pop_matching_dragon(target_list: list, dragon_type_id: int, match_gift_type: bool) -> bool:
    for i, entry in enumerate(target_list):
        if isinstance(entry, dict):
            if entry.get("iid") == dragon_type_id or (match_gift_type and entry.get("type") == dragon_type_id):
                target_list.pop(i)
                return True
        elif isinstance(entry, (str, int)):
            if str(entry) == str(dragon_type_id):
                target_list.pop(i)
                return True
    return False


def remove_stored_dragon(player_data: Dict[str, Any], dragon_type_id: int, is_gift: bool) -> Tuple[bool, str]:
    """Take a dragon out of the gifts or the storage; returns (removed, list name)."""
    removed = False
    list_name = ""

    if is_gift:
        gifts_node = _find_gifts_node(player_data)

        if gifts_node and "dragons" in gifts_node:
            list_name = "gifts -> dragons"
            removed = _pop_matching_dragon(gifts_node["dragons"], dragon_type_id, match_gift_type=True)
    else:
        if "store" in player_data.get("map", {}) and "dragons" in player_data["map"]["store"]:
            list_name = "store -> dragons"
            removed = _pop_matching_dragon(player_data["map"]["store"]["dragons"], dragon_type_id, match_gift_type=False)

    return removed, list_name


def register_owned_dragon(player_data: Dict[str, Any], dragon_type_id: int, dragon_xp: int) -> None:
    """Add the dragon type to the dragon book if it is not there yet."""
    id_str = str(dragon_type_id)
    owned = player_data["map"]["ownedDragons"]
    if id_str in owned:
        return

    for min_xp, entry in _OWNED_DRAGON_STAGES:
        if dragon_xp >= min_xp:
            owned[id_str] = list(entry)
            return
    owned[id_str] = [1, 0, 0]
