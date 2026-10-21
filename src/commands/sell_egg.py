import logging

from src.commands.base import CommandContext, command
from src.enums import Command, Resource
from src.game.items import get_item_config

logger = logging.getLogger(__name__)


@command(Command.SELL_EGG)
def handle(ctx: CommandContext) -> None:
    egg = ctx.find_egg(ctx.uid_arg(0, "egg uid"))

    item_cfg = get_item_config(ctx.game_config, str(egg.get("type")))
    if item_cfg:
        sell_price = item_cfg.get("sell_price", {}).get("g", 0)
        ctx.info[Resource.GOLD] += sell_price
        logger.info("Sold egg of %s for %s gold", item_cfg.get("name"), sell_price)

    ctx.map["eggs"].remove(egg)
