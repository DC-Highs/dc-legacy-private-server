import logging

from dragon_city.commands.base import CommandContext, command
from dragon_city.commands.validation import reject
from dragon_city.enums import Command

logger = logging.getLogger(__name__)

MAX_HELP_ENTRIES = 200


@command(Command.SET_HELP_MAP)
def handle(ctx: CommandContext) -> None:
    help_id = str(ctx.arg(0, "help id"))
    if len(help_id) > 32:
        reject("help id is too long")

    help_map = ctx.private_state.get("helpMap")
    if not isinstance(help_map, list):
        help_map = ctx.private_state["helpMap"] = []

    if help_id in help_map:
        reject(f"the player had already seen help '{help_id}'")
    if len(help_map) >= MAX_HELP_ENTRIES:
        reject("too many help entries")

    help_map.append(help_id)
    logger.info("Help '%s' registered in helpMap", help_id)
