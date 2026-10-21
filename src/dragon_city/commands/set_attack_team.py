import json
import logging

from dragon_city.commands.base import CommandContext, command
from dragon_city.enums import Command

logger = logging.getLogger(__name__)


@command(Command.SET_ATTACK_TEAM)
def handle(ctx: CommandContext) -> None:
    team_type = ctx.args[0]
    team_ids = json.loads(ctx.args[1])

    formatted_team = [{"id": int(dragon_id)} for dragon_id in team_ids]

    if "teams" not in ctx.private_state:
        ctx.private_state["teams"] = {}

    ctx.private_state["teams"][team_type] = formatted_team
    logger.info("Attack team '%s' set: %s", team_type, formatted_team)
