"""Dragon attack training helpers."""
import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

EMPTY_ATTACK_SLOT = -1
ATTACK_SLOTS = 4
DEFAULT_TRAINING_SECONDS = 0
TRAINING_TOLERANCE_SECONDS = 5


def training_time(game_config: Dict[str, Any], attack_id: int) -> int:
    """Seconds an attack takes to train (the config keys attacks by text ids)."""
    attack = game_config.get("attacks", {}).get(str(attack_id), {})
    return int(attack.get("training_time", DEFAULT_TRAINING_SECONDS))


def teach_attack(dragon: Dict[str, Any], attack_id: int, attack_pos: int) -> None:
    """Teach ``attack_id`` to the dragon in slot ``attack_pos`` (0..ATTACK_SLOTS-1)."""
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
        dragon.get("name", "Unknown"), dragon.get("id"), attack_id, old_attack, attack_pos,
    )
