import logging

from src.commands.base import CommandContext, command
from src.commands.validation import MAX_COORDINATE, reject
from src.enums import Command

logger = logging.getLogger(__name__)


@command(Command.PLACE_STORED_ITEM)
def handle(ctx: CommandContext) -> None:
    iso_id = ctx.iso_arg(0)
    item_id = str(ctx.int_arg(1, "item id", 1))
    tx = ctx.int_arg(2, "x", 0, MAX_COORDINATE)
    ty = ctx.int_arg(3, "y", 0, MAX_COORDINATE)

    if iso_id in ctx.map["items"]:
        reject(f"iso id {iso_id} is already used by another object")

    store_items = ctx.map["store"]["items"]
    if item_id not in store_items:
        reject(f"object {item_id} is not in the warehouse")

    if store_items[item_id] > 1:
        store_items[item_id] -= 1
    else:
        del store_items[item_id]

    ctx.map["items"][iso_id] = [int(item_id), tx, ty, 0, 0, 1, {}]
    logger.info("Took object %s out of the warehouse and placed it on the map", item_id)
