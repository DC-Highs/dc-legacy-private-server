import logging

from dragon_city.commands.base import CommandContext, command
from dragon_city.enums import Command, Resource

logger = logging.getLogger(__name__)

ACHIEVEMENT_POINTS = 35


@command(Command.COMPLETE_GOAL)
def handle(ctx: CommandContext) -> None:
    goal_id = int(ctx.args[0])
    goal_config = ctx.game_config.get("goals", {}).get(str(goal_id))

    if not goal_config:
        logger.warning("Goal %s does not exist in the game config", goal_id)
        return

    reward = goal_config.get("reward", {})
    gold_reward = reward.get("g", 0)
    food_reward = reward.get("f", 0)
    cash_reward = reward.get("c", 0)
    xp_reward = reward.get("x", 0)

    info = ctx.info
    if gold_reward > 0:
        info[Resource.GOLD] += gold_reward
    if food_reward > 0:
        info[Resource.FOOD] += food_reward
    if cash_reward > 0:
        info[Resource.CASH] += cash_reward
    if xp_reward > 0:
        info[Resource.XP] += xp_reward

    ctx.private_state["achievement_points"] += ACHIEVEMENT_POINTS

    logger.info("Goal %s completed", goal_id)
    logger.info(
        "Rewards: gold +%s | food +%s | xp +%s | points +%s",
        gold_reward, food_reward, xp_reward, ACHIEVEMENT_POINTS,
    )
    logger.info(
        "Totals: gold %s | food %s | xp %s | points %s",
        info[Resource.GOLD], info[Resource.FOOD], info[Resource.XP], ctx.private_state["achievement_points"],
    )
