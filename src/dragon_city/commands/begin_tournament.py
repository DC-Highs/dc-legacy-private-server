import logging
import time

from dragon_city.commands.base import CommandContext, command
from dragon_city.enums import Command

logger = logging.getLogger(__name__)


@command(Command.BEGIN_TOURNAMENT)
def handle(ctx: CommandContext) -> None:
    current_ts = int(time.time())
    ctx.private_state["beginTournamentTs"] = current_ts

    logger.info("Tournament started, timestamp stored: %s", current_ts)
