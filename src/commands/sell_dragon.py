import logging

from src.commands.base import CommandContext, command
from src.enums import Command, Resource
from src.game.items import get_item_config

logger = logging.getLogger(__name__)


@command(Command.SELL_DRAGON)
def handle(ctx: CommandContext) -> None:
    dragon = ctx.find_dragon(ctx.uid_arg(0, "dragon uid"))

    item_cfg = get_item_config(ctx.game_config, str(dragon.get("type")))
    if item_cfg:
        sell_price = item_cfg.get("sell_price", {}).get("g", 0)
        ctx.info[Resource.GOLD] += sell_price
        logger.info("Sold dragon %s for %s gold", item_cfg.get("name"), sell_price)

    ctx.map["dragons"].remove(dragon)
