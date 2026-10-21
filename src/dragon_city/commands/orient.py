import logging

from dragon_city.commands.base import CommandContext, command
from dragon_city.enums import Command

logger = logging.getLogger(__name__)


@command(Command.ORIENT)
def handle(ctx: CommandContext) -> None:
    iso_id = str(ctx.args[0])
    frame = ctx.args[1]

    items = ctx.map["items"]
    if iso_id not in items:
        logger.warning("Object with iso id %s not found on the map", iso_id)
        return

    items[iso_id][4] = frame
    logger.info("Rotated object %s to frame %s", iso_id, frame)
