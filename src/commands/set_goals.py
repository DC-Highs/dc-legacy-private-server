import json
import logging

from src.commands.base import CommandContext, command
from src.commands.validation import check_json_depth, reject
from src.enums import Command

logger = logging.getLogger(__name__)

GOALS_SLOTS = 170
MAX_GOAL_ID = 999


@command(Command.SET_GOALS)
def handle(ctx: CommandContext) -> None:
    goal_id = ctx.int_arg(0, "goal id", 0, MAX_GOAL_ID)
    raw_state = ctx.text_arg(1, "goal state", 256, allow_empty=True)
    try:
        goal_state = json.loads(raw_state, parse_constant=lambda _c: reject("goal state has an invalid number"))
    except ValueError:
        reject("goal state is not valid JSON")
    check_json_depth(goal_state, "goal state", max_depth=2, max_items=32)

    if not isinstance(ctx.private_state.get("goals"), list):
        ctx.private_state["goals"] = [None] * GOALS_SLOTS

    goals = ctx.private_state["goals"]
    while len(goals) <= goal_id:
        goals.append(None)

    goals[goal_id] = goal_state

    logger.info("Goal %s set to state %s", goal_id, goal_state)
