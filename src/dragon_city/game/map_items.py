"""Helpers for the items placed on the player's map."""
import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)

ATTRIBUTES_INDEX = 6


def clear_habitat_arrival(player_data: Dict[str, Any], habitat_id: str, current_ts: int) -> None:
    """Replace the 'ar' (awaiting resident) flag of a habitat by its last-activity timestamp."""
    items = player_data["map"]["items"]
    if habitat_id not in items:
        return

    item_data = items[habitat_id]
    if len(item_data) > ATTRIBUTES_INDEX and isinstance(item_data[ATTRIBUTES_INDEX], dict):
        attributes = item_data[ATTRIBUTES_INDEX]
        if "ar" in attributes:
            attributes["lat"] = current_ts
            del attributes["ar"]
            logger.info("Habitat %s: removed 'ar' and set 'lat' to %s", habitat_id, current_ts)
