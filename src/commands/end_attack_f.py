import logging
import time

from src.commands.base import CommandContext, command
from src.commands.validation import reject
from src.enums import Command
from src.game.combat import apply_kills, parse_kills_log

logger = logging.getLogger(__name__)

PVP_WIN_POINTS = 35
LEAGUE_COMPLETE_POINTS = 120
LEAGUE_WIN_THRESHOLD = 7
# A fight cannot be over the instant it began, and a pending attack goes stale.
MIN_FIGHT_SECONDS = 10
MAX_FIGHT_SECONDS = 3600


@command(Command.END_ATTACK_F)
def handle(ctx: CommandContext) -> None:
    args = ctx.args
    target_player_id = str(ctx.int_arg(0, "opponent id", 1))
    position = ctx.int_arg(1, "position", 0, 1000)
    win_status = ctx.flag_arg(2, "win status")
    kills_log = parse_kills_log(args[3]) if len(args) > 3 else {}

    # The fight must have been started with attack_player, and it can only be reported once.
    now = int(time.time())
    attacks_sent = ctx.private_state.get("attacksSent")
    pending = next(
        (a for a in reversed(attacks_sent if isinstance(attacks_sent, list) else [])
         if isinstance(a, dict) and a.get("victim_id") == target_player_id),
        None,
    )
    if pending is None:
        reject(f"no attack against {target_player_id} is in progress")
    fight_seconds = now - int(pending.get("time", 0))
    if not MIN_FIGHT_SECONDS <= fight_seconds <= MAX_FIGHT_SECONDS:
        reject(f"the attack against {target_player_id} lasted {fight_seconds}s, which is not plausible")
    attacks_sent.remove(pending)

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
