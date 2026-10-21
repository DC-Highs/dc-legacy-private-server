import logging

from dragon_city.commands.base import CommandContext, command
from dragon_city.enums import Command

logger = logging.getLogger(__name__)


@command(Command.PLACE_STORED_ITEM)
def handle(ctx: CommandContext) -> None:
    iso_id = str(ctx.args[0])
    item_id = str(ctx.args[1])
    tx = ctx.args[2]
    ty = ctx.args[3]

    item_found = False
    if "store" in ctx.map and "items" in ctx.map["store"]:
        store_items = ctx.map["store"]["items"]
        if item_id in store_items:
            item_found = True

            if store_items[item_id] > 1:
                store_items[item_id] -= 1
            else:
                del store_items[item_id]

            if not store_items:
                del ctx.map["store"]["items"]

    if not item_found:
        logger.warning("Tried to place object %s but it is not in the warehouse", item_id)
        return

    ctx.map["items"][iso_id] = [int(item_id), int(tx), int(ty), 0, 0, 1, {}]
    logger.info("Took object %s out of the warehouse and placed it on the map", item_id)
