import logging

from dragon_city.commands.base import CommandContext, command
from dragon_city.enums import Command

logger = logging.getLogger(__name__)


@command(Command.SET_HELP_MAP)
def handle(ctx: CommandContext) -> None:
    help_id = str(ctx.args[0])

    if "helpMap" not in ctx.private_state:
        ctx.private_state["helpMap"] = []

    help_map = ctx.private_state["helpMap"]
    if help_id in help_map:
        logger.warning("The player had already seen help '%s'", help_id)
        return

    help_map.append(help_id)
    logger.info("Help '%s' registered in helpMap", help_id)
