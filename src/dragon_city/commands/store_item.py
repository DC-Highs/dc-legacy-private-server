import logging

from dragon_city.commands.base import CommandContext, command
from dragon_city.enums import Command

logger = logging.getLogger(__name__)


@command(Command.STORE_ITEM)
def handle(ctx: CommandContext) -> None:
    iso_id = str(ctx.args[0])

    items = ctx.map["items"]
    if iso_id not in items:
        logger.warning("Object with iso id %s does not exist on the map", iso_id)
        return

    item_id = str(items[iso_id][0])
    del items[iso_id]

    if "store" not in ctx.map:
        ctx.map["store"] = {}
    if "items" not in ctx.map["store"]:
        ctx.map["store"]["items"] = {}

    stored_items = ctx.map["store"]["items"]
    if item_id in stored_items:
        stored_items[item_id] += 1
    else:
        stored_items[item_id] = 1

    logger.info("Stored object %s (iso id %s) in the warehouse", item_id, iso_id)
