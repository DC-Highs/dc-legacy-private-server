import logging

from dragon_city.commands.base import CommandContext, command
from dragon_city.enums import Command, Resource
from dragon_city.game.items import get_item_config

logger = logging.getLogger(__name__)


@command(Command.SELL_EGG)
def handle(ctx: CommandContext) -> None:
    egg_uid = ctx.args[0]
    eggs = ctx.map["eggs"]
    egg_index = next((i for i, e in enumerate(eggs) if e.get("id") == egg_uid), None)

    if egg_index is None:
        logger.warning("Egg with uid %s not found", egg_uid)
        return

    dragon_type = str(eggs[egg_index].get("type"))

    item_cfg = get_item_config(ctx.game_config, dragon_type)
    if item_cfg:
        sell_price = item_cfg.get("sell_price", {}).get("g", 0)
        ctx.info[Resource.GOLD] += sell_price
        logger.info("Sold egg of %s for %s gold", item_cfg.get("name"), sell_price)

    eggs.pop(egg_index)
