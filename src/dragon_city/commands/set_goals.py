import json
import logging

from dragon_city.commands.base import CommandContext, command
from dragon_city.enums import Command

logger = logging.getLogger(__name__)

GOALS_SLOTS = 170


@command(Command.SET_GOALS)
def handle(ctx: CommandContext) -> None:
    goal_id = int(ctx.args[0])
    goal_state = json.loads(ctx.args[1])

    if "goals" not in ctx.private_state:
        ctx.private_state["goals"] = [None] * GOALS_SLOTS

    goals = ctx.private_state["goals"]
    while len(goals) <= goal_id:
        goals.append(None)

    goals[goal_id] = goal_state

    logger.info("Goal %s set to state %s", goal_id, goal_state)
