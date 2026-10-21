import logging

from dragon_city.commands.base import CommandContext, command
from dragon_city.enums import Command

logger = logging.getLogger(__name__)


@command(Command.MOVE)
def handle(ctx: CommandContext) -> None:
    iso_id = str(ctx.args[0])
    tx = ctx.args[1]
    ty = ctx.args[2]
    frame = ctx.args[3]

    items = ctx.map["items"]
    if iso_id not in items:
        logger.warning("Object with iso id %s not found on the map", iso_id)
        return

    items[iso_id][1] = tx
    items[iso_id][2] = ty
    items[iso_id][4] = frame

    logger.info("Moved object %s to (%s, %s) with rotation %s", iso_id, tx, ty, frame)
