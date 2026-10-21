import logging

from dragon_city.commands.base import CommandContext, command
from dragon_city.enums import Command, Resource
from dragon_city.game.items import get_item_config

logger = logging.getLogger(__name__)


@command(Command.SELL_STORED_DRAGON)
def handle(ctx: CommandContext) -> None:
    dragon_id = int(ctx.args[0])
    dragon_lvl = int(ctx.args[1])
    is_gift = int(ctx.args[2])

    item_cfg = get_item_config(ctx.game_config, dragon_id)
    if not item_cfg:
        logger.warning("Dragon %s does not exist in the game config", dragon_id)
        return

    sell_price = item_cfg.get("sell_price", {}).get("g", 0)

    target_list = None
    list_name = ""

    if is_gift == 1:
        if "privateState" in ctx.player_data and "gifts" in ctx.private_state:
            target_list = ctx.private_state["gifts"]
            list_name = "gifts"
    else:
        if "store" in ctx.player_data.get("map", {}) and "dragons" in ctx.map["store"]:
            target_list = ctx.map["store"]["dragons"]
            list_name = "store"

    if target_list is None:
        logger.warning("sell_stored_dragon failed: target list (is_gift=%s) does not exist in the player save", is_gift)
        return

    index_to_remove = -1
    for i, d in enumerate(target_list):
        if d.get("iid") == dragon_id and d.get("lvl") == dragon_lvl:
            index_to_remove = i
            break

    if index_to_remove == -1:
        logger.warning("sell_stored_dragon failed: dragon %s level %s not found in %s", dragon_id, dragon_lvl, list_name)
        return

    target_list.pop(index_to_remove)
    ctx.info[Resource.GOLD] += sell_price

    logger.info("Sold dragon %s (level %s) from %s", item_cfg.get("name", dragon_id), dragon_lvl, list_name)
    logger.info("Gold added: +%s | new balance: %s", sell_price, ctx.info[Resource.GOLD])
