import logging
import time

from dragon_city.commands.base import CommandContext, command
from dragon_city.enums import Command
from dragon_city.game.levels import level_from_xp
from dragon_city.storage import PVP_PLAYERS_FILE, load_pvp_players

logger = logging.getLogger(__name__)


@command(Command.ATTACK_PLAYER)
def handle(ctx: CommandContext) -> None:
    target_player_id = str(ctx.args[0])
    current_time = int(time.time())

    units = []

    try:
        pvp_db = load_pvp_players()

        if target_player_id in pvp_db:
            victim_data = pvp_db[target_player_id]

            pvp_team_ids = [
                d["id"] for d in victim_data.get("privateState", {}).get("teams", {}).get("pvp", [])
            ]
            dragons_by_id = {d["id"]: d for d in victim_data.get("map", {}).get("dragons", [])}

            for dragon_id in pvp_team_ids:
                dragon = dragons_by_id.get(dragon_id)
                if dragon:
                    units.append({
                        "name": dragon.get("name", "Dragon"),
                        "type": dragon["type"],
                        "lvl": level_from_xp(dragon.get("xp", 0), dragon["type"]),
                        "id": dragon["id"],
                    })
        else:
            logger.warning("Opponent %s does not exist in %s", target_player_id, PVP_PLAYERS_FILE)

    except Exception:
        logger.exception("Failed to read %s", PVP_PLAYERS_FILE)

    if "privateState" not in ctx.player_data:
        ctx.player_data["privateState"] = {}
    if "attacksSent" not in ctx.private_state:
        ctx.private_state["attacksSent"] = []

    ctx.private_state["attacksSent"].append({"victim_id": target_player_id, "time": current_time})

    logger.info("Starting PvP combat against %s", target_player_id)

    ctx.result = units
