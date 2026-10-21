import json
import logging

from dragon_city.commands.base import CommandContext, command
from dragon_city.enums import Command
from dragon_city.game.combat import apply_kills

logger = logging.getLogger(__name__)

PVP_WIN_POINTS = 35
LEAGUE_COMPLETE_POINTS = 120
LEAGUE_WIN_THRESHOLD = 7


@command(Command.END_ATTACK_F)
def handle(ctx: CommandContext) -> None:
    args = ctx.args
    target_player_id = str(args[0])
    position = int(args[1])
    win_status = int(args[2])

    kills_log = {}
    if len(args) > 3 and args[3]:
        try:
            kills_log = json.loads(args[3])
        except Exception:
            logger.exception("Failed to decode kills_log")

    private_state = ctx.private_state

    if win_status == 1:
        if "universAttackWin" not in ctx.map:
            ctx.map["universAttackWin"] = []

        attack_win_list = ctx.map["universAttackWin"]
        private_state["achievement_points"] += PVP_WIN_POINTS

        target_found = False
        for i, entry in enumerate(attack_win_list):
            if isinstance(entry, list) and len(entry) >= 3:
                if str(entry[0]) == target_player_id:
                    attack_win_list[i] = position
                    target_found = True
                    break

        if not target_found:
            attack_win_list.append(position)

    apply_kills(ctx.player_data, kills_log)

    logger.info("Combat against %s processed (%s)", target_player_id, "victory" if win_status == 1 else "defeat")
    logger.info("Points earned: %s | total points: %s", PVP_WIN_POINTS, private_state["achievement_points"])

    victories = len(ctx.map.get("universAttackWin", []))

    if win_status == 1 and victories >= LEAGUE_WIN_THRESHOLD:
        ctx.info["pvpLevel"] = ctx.info.get("pvpLevel", 1) + 1
        private_state["achievement_points"] += LEAGUE_COMPLETE_POINTS
        ctx.map["universAttackWin"] = []
        ctx.result = True
        logger.info("League completed, new pvpLevel: %s", ctx.info["pvpLevel"])
        logger.info("Points earned: %s | total points: %s", LEAGUE_COMPLETE_POINTS, private_state["achievement_points"])
    else:
        ctx.result = None
