import logging

from dragon_city.commands.base import CommandContext, command
from dragon_city.commands.validation import reject
from dragon_city.enums import Command, Resource

logger = logging.getLogger(__name__)

ACHIEVEMENT_POINTS = 35
MAX_GOAL_ID = 9999


@command(Command.COMPLETE_GOAL)
def handle(ctx: CommandContext) -> None:
    goal_id = ctx.int_arg(0, "goal id", 0, MAX_GOAL_ID)
    goal_config = ctx.game_config.get("goals", {}).get(str(goal_id))

    if not goal_config:
        reject(f"goal {goal_id} does not exist in the game config")

    # A goal pays out once; the client could otherwise claim it again and again.
    completed = ctx.private_state.setdefault("completedGoals", [])
    if goal_id in completed:
        reject(f"goal {goal_id} was already completed")
    completed.append(goal_id)

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
