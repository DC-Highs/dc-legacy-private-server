import logging

from dragon_city.commands.base import CommandContext, command
from dragon_city.enums import Command

logger = logging.getLogger(__name__)


@command(Command.RENAME_DRAGON)
def handle(ctx: CommandContext) -> None:
    dragon_id = ctx.args[0]
    new_name = str(ctx.args[1])

    for dragon in ctx.player_data.get("map", {}).get("dragons", []):
        if dragon.get("id") == dragon_id:
            dragon["name"] = new_name
            logger.info("Dragon %s renamed to: %s", dragon_id, new_name)
            return

    logger.warning("Dragon with id %s not found in the player save", dragon_id)
