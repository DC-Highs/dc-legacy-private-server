import logging

from src.commands.base import CommandContext, command
from src.enums import Command

logger = logging.getLogger(__name__)


@command(Command.CLEAN_RECEIVED_ASSISTS)
def handle(ctx: CommandContext) -> None:
    helper_pid = str(ctx.int_arg(0, "helper id", 1))
    key = "u" + helper_pid

    received = ctx.map.get("receivedAssists", {})
    if isinstance(received, dict) and key in received:
        del received[key]

    logger.info("Removed the assist entry of neighbor %s", helper_pid)
