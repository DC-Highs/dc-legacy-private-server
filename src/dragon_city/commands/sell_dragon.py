import logging

from dragon_city.commands.base import CommandContext, command
from dragon_city.enums import Command, Resource
from dragon_city.game.items import get_item_config

logger = logging.getLogger(__name__)


@command(Command.SELL_DRAGON)
def handle(ctx: CommandContext) -> None:
    dragon_uid = ctx.args[0]
    dragons = ctx.map["dragons"]
    dragon_index = next((i for i, d in enumerate(dragons) if d.get("id") == dragon_uid), None)

    if dragon_index is None:
        logger.warning("Dragon with uid %s not found", dragon_uid)
        return

    dragon_type = str(dragons[dragon_index].get("type"))

    item_cfg = get_item_config(ctx.game_config, dragon_type)
    if item_cfg:
        sell_price = item_cfg.get("sell_price", {}).get("g", 0)
        ctx.info[Resource.GOLD] += sell_price
        logger.info("Sold dragon %s for %s gold", item_cfg.get("name"), sell_price)

    dragons.pop(dragon_index)
