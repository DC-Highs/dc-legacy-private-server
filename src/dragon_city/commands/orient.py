import logging

from dragon_city.commands.base import CommandContext, command
from dragon_city.commands.validation import MAX_SMALL_INT
from dragon_city.enums import Command

logger = logging.getLogger(__name__)


@command(Command.ORIENT)
def handle(ctx: CommandContext) -> None:
    iso_id = ctx.iso_arg(0)
    frame = ctx.int_arg(1, "frame", 0, MAX_SMALL_INT)

    ctx.map_item(iso_id)[4] = frame
    logger.info("Rotated object %s to frame %s", iso_id, frame)
