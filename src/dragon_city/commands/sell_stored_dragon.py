import logging

from dragon_city.commands.base import CommandContext, command
from dragon_city.commands.validation import reject
from dragon_city.enums import Command, Resource

logger = logging.getLogger(__name__)


@command(Command.SELL_STORED_DRAGON)
def handle(ctx: CommandContext) -> None:
    dragon_id = ctx.int_arg(0, "dragon id", 1)
    dragon_lvl = ctx.int_arg(1, "dragon level", 0, 100)
    is_gift = ctx.flag_arg(2, "is gift")

    item_cfg = ctx.item_config(dragon_id)
    sell_price = item_cfg.get("sell_price", {}).get("g", 0)

    if is_gift == 1:
        target_list = ctx.private_state.get("gifts")
        list_name = "gifts"
    else:
        target_list = ctx.map["store"]["dragons"]
        list_name = "store"

    if not isinstance(target_list, list):
        reject(f"target list (is_gift={is_gift}) does not exist in the player save")

    index_to_remove = next(
        (i for i, d in enumerate(target_list)
         if isinstance(d, dict) and d.get("iid") == dragon_id and d.get("lvl") == dragon_lvl),
        -1,
    )
    if index_to_remove == -1:
        reject(f"dragon {dragon_id} level {dragon_lvl} not found in {list_name}")

    target_list.pop(index_to_remove)
    ctx.info[Resource.GOLD] += sell_price

    logger.info("Sold dragon %s (level %s) from %s", item_cfg.get("name", dragon_id), dragon_lvl, list_name)
    logger.info("Gold added: +%s | new balance: %s", sell_price, ctx.info[Resource.GOLD])
