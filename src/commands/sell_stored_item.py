import logging

from src.commands.base import CommandContext, command
from src.commands.validation import reject
from src.enums import Command, Resource

logger = logging.getLogger(__name__)


@command(Command.SELL_STORED_ITEM)
def handle(ctx: CommandContext) -> None:
    item_id_to_sell = str(ctx.int_arg(0, "item id", 1))
    item_cfg = ctx.item_config(item_id_to_sell)

    sell_price = item_cfg.get("sell_price", {}).get("g", 0)
    store_items = ctx.map["store"]["items"]

    if item_id_to_sell not in store_items:
        reject(f"the player has no item {item_id_to_sell} in the warehouse")

    if store_items[item_id_to_sell] > 1:
        store_items[item_id_to_sell] -= 1
        logger.info("Sold %s, %s left", item_cfg.get("name", item_id_to_sell), store_items[item_id_to_sell])
    else:
        del store_items[item_id_to_sell]
        logger.info("Sold %s, last unit removed from the warehouse", item_cfg.get("name", item_id_to_sell))

    ctx.info[Resource.GOLD] += sell_price
    logger.info("Gold added: +%s | new balance: %s", sell_price, ctx.info[Resource.GOLD])
