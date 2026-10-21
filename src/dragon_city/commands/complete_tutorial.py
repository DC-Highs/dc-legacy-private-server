import logging

from dragon_city.commands.base import CommandContext, command
from dragon_city.enums import Command

logger = logging.getLogger(__name__)


@command(Command.COMPLETE_TUTORIAL)
def handle(ctx: CommandContext) -> None:
    ctx.info["completed_tutorial"] = str(ctx.int_arg(0, "tutorial step", 0, 1000))

    logger.info("Tutorial marked as completed")
