"""Combat bookkeeping shared by tournaments and PvP."""
import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)


def apply_kills(player_data: Dict[str, Any], kills_log: Dict[str, Any]) -> None:
    """Add the kills reported by the client (keyed by dragon id) to each dragon's counter."""
    if not kills_log or "dragons" not in player_data.get("map", {}):
        return

    for dragon in player_data["map"]["dragons"]:
        dragon_id_str = str(dragon.get("id"))

        if dragon_id_str in kills_log:
            kills_to_add = int(kills_log[dragon_id_str])
            dragon["nbKill"] = dragon.get("nbKill", 0) + kills_to_add

            logger.info(
                "Dragon %s (id=%s) gained %s kills, total: %s",
                dragon.get("name", "Unknown"), dragon_id_str, kills_to_add, dragon["nbKill"],
            )
