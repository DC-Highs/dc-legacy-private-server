import logging

from src.commands.base import CommandContext, command
from src.enums import Command

logger = logging.getLogger(__name__)


@command(Command.PING)
def handle(ctx: CommandContext) -> None:
    logger.debug("Keep-alive received from the client")
