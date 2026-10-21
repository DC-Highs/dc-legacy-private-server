import logging

from dragon_city.commands.base import CommandContext, command
from dragon_city.enums import Command

logger = logging.getLogger(__name__)


@command(Command.CLEAN_RECEIVED_ASSISTS)
def handle(ctx: CommandContext) -> None:
    helper_pid = str(ctx.args[0])
    key = "u" + helper_pid

    received = ctx.player_data.get("map", {}).get("receivedAssists", {})
    if isinstance(received, dict) and key in received:
        del received[key]

    logger.info("Removed the assist entry of neighbor %s", helper_pid)
