"""Dragon attack training helpers."""
import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

EMPTY_ATTACK_SLOT = -1
ATTACK_SLOTS = 4


def teach_attack(player_data: Dict[str, Any], dragon_uid: str, attack_id: int, attack_pos: int) -> bool:
    """Teach ``attack_id`` to the dragon in slot ``attack_pos``; returns whether the dragon exists."""
    for dragon in player_data.get("map", {}).get("dragons", []):
        if str(dragon.get("id")) != dragon_uid:
            continue

        if "attack" not in dragon or not isinstance(dragon["attack"], list):
            dragon["attack"] = [EMPTY_ATTACK_SLOT] * ATTACK_SLOTS

        attacks: List[int] = dragon["attack"]
        while len(attacks) <= attack_pos:
            attacks.append(EMPTY_ATTACK_SLOT)

        old_attack = attacks[attack_pos]
        attacks[attack_pos] = attack_id

        dragon["work_id"] = []

        logger.info(
            "Dragon %s (id=%s) learned attack %s (replacing %s in slot %s)",
            dragon.get("name", "Unknown"), dragon_uid, attack_id, old_attack, attack_pos,
        )
        return True

    return False
