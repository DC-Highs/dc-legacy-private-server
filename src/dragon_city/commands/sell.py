import logging

from dragon_city.commands.base import CommandContext, command
from dragon_city.enums import Command, Resource
from dragon_city.game.items import get_item_config

logger = logging.getLogger(__name__)


@command(Command.SELL)
def handle(ctx: CommandContext) -> None:
    iso_id = str(ctx.args[0])
    reason = ctx.args[1] if len(ctx.args) > 1 else "UNKNOWN"

    items = ctx.map["items"]
    if iso_id not in items:
        return

    item_type_id = str(items[iso_id][0])

    item_cfg = get_item_config(ctx.game_config, item_type_id)
    if item_cfg:
        sell_price = item_cfg.get("sell_price", {}).get("g", 0)
        ctx.info[Resource.GOLD] += sell_price
        logger.info("Sold %s for %s gold (reason: %s)", item_cfg.get("name"), sell_price, reason)
    else:
        logger.warning("Object %s does not exist in the game config", item_type_id)

    del items[iso_id]
