import logging
import time

from dragon_city.commands.base import CommandContext, command
from dragon_city.commands.validation import reject
from dragon_city.enums import Command
from dragon_city.game.levels import level_from_xp
from dragon_city.game.pvp import get_pvp_player

logger = logging.getLogger(__name__)

MAX_PENDING_ATTACKS = 20


@command(Command.ATTACK_PLAYER)
def handle(ctx: CommandContext) -> None:
    target_player_id = str(ctx.int_arg(0, "opponent id", 1))

    victim_data = get_pvp_player(target_player_id)
    if victim_data is None:
        reject(f"opponent {target_player_id} does not exist")

    pvp_team_ids = [d["id"] for d in victim_data.get("privateState", {}).get("teams", {}).get("pvp", [])]
    dragons_by_id = {d["id"]: d for d in victim_data.get("map", {}).get("dragons", [])}

    units = []
    for dragon_id in pvp_team_ids:
        dragon = dragons_by_id.get(dragon_id)
        if dragon:
            units.append({
                "name": dragon.get("name", "Dragon"),
                "type": dragon["type"],
                "lvl": level_from_xp(dragon.get("xp", 0), dragon["type"]),
                "id": dragon["id"],
            })

    attacks_sent = ctx.private_state.get("attacksSent")
    if not isinstance(attacks_sent, list):
        attacks_sent = ctx.private_state["attacksSent"] = []

    attacks_sent.append({"victim_id": target_player_id, "time": int(time.time())})
    del attacks_sent[:-MAX_PENDING_ATTACKS]

    logger.info("Starting PvP combat against %s", target_player_id)

    ctx.result = units
