import logging

from dragon_city.commands.base import CommandContext, command
from dragon_city.enums import Command, Resource
from dragon_city.game.items import get_item_config

logger = logging.getLogger(__name__)


@command(Command.SELL_STORED_ITEM)
def handle(ctx: CommandContext) -> None:
    item_id_to_sell = str(ctx.args[0])
    item_cfg = get_item_config(ctx.game_config, item_id_to_sell)

    if not item_cfg:
        logger.warning("Object %s does not exist in the game config", item_id_to_sell)
        return

    sell_price = item_cfg.get("sell_price", {}).get("g", 0)

    if "store" not in ctx.map or "items" not in ctx.map["store"]:
        logger.warning("sell_stored_item failed: the player has no ['map']['store']['items'] key")
        return

    store_items = ctx.map["store"]["items"]

    if item_id_to_sell not in store_items:
        logger.warning("sell_stored_item failed: the player has no item %s in the warehouse", item_id_to_sell)
        return

    if store_items[item_id_to_sell] > 1:
        store_items[item_id_to_sell] -= 1
        logger.info("Sold %s, %s left", item_cfg.get("name", item_id_to_sell), store_items[item_id_to_sell])
    else:
        del store_items[item_id_to_sell]
        logger.info("Sold %s, last unit removed from the warehouse", item_cfg.get("name", item_id_to_sell))

    ctx.info[Resource.GOLD] += sell_price
    logger.info("Gold added: +%s | new balance: %s", sell_price, ctx.info[Resource.GOLD])
