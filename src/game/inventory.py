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
    for container in (player_data, player_data.get("privateState", {}), player_data.get("map", {})):
        if "gifts" in container:
            return container["gifts"]
    return None


def _entry_matches(entry: Any, dragon_type_id: int, level: int, is_gift: bool) -> bool:
    if isinstance(entry, dict):
        if is_gift:
            return entry.get("iid") == dragon_type_id or entry.get("type") == dragon_type_id
        if entry.get("iid") != dragon_type_id:
            return False
        stored_level = entry.get("lvl", 0)
        # Freshly won dragons are stored at level 0 and the client may report 0 or 1 for them.
        return stored_level == level or (stored_level == 0 and level in (0, 1))
    if isinstance(entry, (str, int)):
        return str(entry) == str(dragon_type_id)
    return False


def take_stored_dragon(
    player_data: Dict[str, Any], dragon_type_id: int, level: int, is_gift: bool
) -> Tuple[Optional[int], str]:
    """Remove a dragon from the gifts or the storage.

    Returns the level it had (never below 1) or ``None`` when the player does not own
    it, plus the name of the list that was searched. The caller must use the returned
    level, never the one the client claims.
    """
    if is_gift:
        gifts_node = _find_gifts_node(player_data)
        target_list = gifts_node.get("dragons") if isinstance(gifts_node, dict) else None
        list_name = "gifts -> dragons"
    else:
        target_list = player_data.get("map", {}).get("store", {}).get("dragons")
        list_name = "store -> dragons"

    if not isinstance(target_list, list):
        return None, list_name

    for index, entry in enumerate(target_list):
        if _entry_matches(entry, dragon_type_id, level, is_gift):
            target_list.pop(index)
            stored_level = entry.get("lvl", 0) if isinstance(entry, dict) else 0
            return max(1, stored_level), list_name
    return None, list_name


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
