import logging

from dragon_city.commands.base import CommandContext, command
from dragon_city.enums import Command

logger = logging.getLogger(__name__)


@command(Command.PING)
def handle(ctx: CommandContext) -> None:
    logger.debug("Keep-alive received from the client")
