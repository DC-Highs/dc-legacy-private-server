import logging

from src.commands.base import CommandContext, command
from src.enums import Command

logger = logging.getLogger(__name__)


@command(Command.SYNC)
def handle(ctx: CommandContext) -> None:
    logger.info("Sync ping received, returning the current state")
