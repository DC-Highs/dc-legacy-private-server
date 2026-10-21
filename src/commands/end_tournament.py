import logging
import time

from src.commands.base import CommandContext, command
from src.commands.validation import reject
from src.enums import Command, Resource
from src.game.combat import apply_kills, parse_kills_log

logger = logging.getLogger(__name__)

ACHIEVEMENT_POINTS = 50
MIN_TOURNAMENT_SECONDS = 5


@command(Command.END_TOURNAMENT)
def handle(ctx: CommandContext) -> None:
    player_won = ctx.flag_arg(0, "won") == 1
    kills_log = parse_kills_log(ctx.args[1]) if len(ctx.args) > 1 else {}

    # A tournament can only end after it began, and only once.
    now = int(time.time())
    begin_ts = int(ctx.private_state.get("beginTournamentTs") or 0)
    end_ts = int(ctx.private_state.get("endTournamentTs") or 0)
    if begin_ts <= end_ts or now - begin_ts < MIN_TOURNAMENT_SECONDS:
        reject("there is no tournament in progress")

    ctx.private_state["endTournamentTs"] = now

    logger.info("Tournament ended: %s. Kills: %s", "won" if player_won else "lost", kills_log)

    apply_kills(ctx.player_data, kills_log)

    if not player_won:
        return

    current_tourney = str(ctx.private_state.get("currentTournament", 1))
    tournaments_db = ctx.game_config.get("tournaments", {})

    if current_tourney not in tournaments_db:
        logger.warning("Tournament %s does not exist in the game config", current_tourney)
        return

    rewards = tournaments_db[current_tourney].get("reward", {}).get("resources", {})

    gold_reward = rewards.get("g", 0)
    food_reward = rewards.get("f", 0)
    cash_reward = rewards.get("c", 0)

    info = ctx.info
    if gold_reward > 0:
        info[Resource.GOLD] += gold_reward
    if food_reward > 0:
        info[Resource.FOOD] += food_reward
    if cash_reward > 0:
        info[Resource.CASH] += cash_reward

    ctx.private_state["currentTournament"] = int(current_tourney) + 1
    ctx.private_state["achievement_points"] += ACHIEVEMENT_POINTS

    logger.info("Tournament %s completed", current_tourney)
    logger.info(
        "Rewards added -> gold: %s | food: %s | gems: %s | points: %s",
        gold_reward, food_reward, cash_reward, ACHIEVEMENT_POINTS,
    )
    logger.info("Next tournament: %s", ctx.private_state["currentTournament"])
