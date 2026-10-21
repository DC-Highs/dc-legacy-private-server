import logging

from dragon_city.commands.base import CommandContext, command
from dragon_city.commands.validation import MAX_COORDINATE, MAX_SMALL_INT
from dragon_city.enums import Command

logger = logging.getLogger(__name__)


@command(Command.MOVE)
def handle(ctx: CommandContext) -> None:
    iso_id = ctx.iso_arg(0)
    tx = ctx.int_arg(1, "x", 0, MAX_COORDINATE)
    ty = ctx.int_arg(2, "y", 0, MAX_COORDINATE)
    frame = ctx.int_arg(3, "frame", 0, MAX_SMALL_INT)

    item = ctx.map_item(iso_id)
    item[1] = tx
    item[2] = ty
    item[4] = frame

    logger.info("Moved object %s to (%s, %s) with rotation %s", iso_id, tx, ty, frame)
