import logging

from dragon_city.commands.base import CommandContext, command
from dragon_city.enums import Command

logger = logging.getLogger(__name__)


@command(Command.SYNC)
def handle(ctx: CommandContext) -> None:
    logger.info("Sync ping received, returning the current state")
