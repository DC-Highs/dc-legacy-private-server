import logging

from src.commands.base import CommandContext, command
from src.enums import Command

logger = logging.getLogger(__name__)


@command(Command.RENAME_DRAGON)
def handle(ctx: CommandContext) -> None:
    dragon = ctx.find_dragon(ctx.uid_arg(0, "dragon uid"))
    dragon["name"] = ctx.text_arg(1, "dragon name")

    logger.info("Dragon %s renamed to: %s", dragon.get("id"), dragon["name"])
