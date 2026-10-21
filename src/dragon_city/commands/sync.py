import logging

from dragon_city.commands.base import CommandContext, command
from dragon_city.enums import Command

logger = logging.getLogger(__name__)


@command(Command.SYNC)
def handle(ctx: CommandContext) -> None:
    random_ping = ctx.args[0] if len(ctx.args) > 0 else "unknown"

    logger.info("Sync ping received (hash: %s), returning the current state", random_ping)
