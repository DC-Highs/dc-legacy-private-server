import logging

from src.commands.base import CommandContext, command
from src.enums import Command

logger = logging.getLogger(__name__)


@command(Command.STORE_ITEM)
def handle(ctx: CommandContext) -> None:
    iso_id = ctx.iso_arg(0)

    item_id = str(ctx.map_item(iso_id)[0])
    del ctx.map["items"][iso_id]

    stored_items = ctx.map["store"]["items"]
    stored_items[item_id] = stored_items.get(item_id, 0) + 1

    logger.info("Stored object %s (iso id %s) in the warehouse", item_id, iso_id)
