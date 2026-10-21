"""Combat bookkeeping shared by tournaments and PvP."""
import json
import logging
from typing import Any, Dict

from src.commands.validation import check_json_depth, reject, to_int

logger = logging.getLogger(__name__)

MAX_KILLS_PER_DRAGON = 1000
MAX_KILLS_ENTRIES = 20


def parse_kills_log(raw: Any) -> Dict[str, int]:
    """Parse the ``{dragon id: kills}`` JSON reported by the client."""
    if raw in (None, "", []):
        return {}
    if not isinstance(raw, str) or len(raw) > 2000:
        reject("kills log must be a short JSON text")
    try:
        parsed = json.loads(raw, parse_constant=lambda _c: reject("kills log has an invalid number"))
    except ValueError:
        reject("kills log is not valid JSON")
    if parsed in ({}, []):
        return {}
    if not isinstance(parsed, dict) or len(parsed) > MAX_KILLS_ENTRIES:
        reject("kills log must be a small object")
    check_json_depth(parsed, "kills log", max_depth=1, max_items=MAX_KILLS_ENTRIES + 1)
    return {str(key): to_int(value, "kills", 0, MAX_KILLS_PER_DRAGON) for key, value in parsed.items()}


def apply_kills(player_data: Dict[str, Any], kills_log: Dict[str, int]) -> None:
    """Add the kills reported by the client (keyed by dragon id) to each dragon's counter."""
    if not kills_log:
        return

    for dragon in player_data["map"]["dragons"]:
        dragon_id_str = str(dragon.get("id"))

        if dragon_id_str in kills_log:
            kills_to_add = kills_log[dragon_id_str]
            dragon["nbKill"] = dragon.get("nbKill", 0) + kills_to_add

            logger.info(
                "Dragon %s (id=%s) gained %s kills, total: %s",
                dragon.get("name", "Unknown"), dragon_id_str, kills_to_add, dragon["nbKill"],
            )
