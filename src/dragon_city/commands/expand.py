import logging

from dragon_city.commands.base import CommandContext, command
from dragon_city.enums import Command, Resource

logger = logging.getLogger(__name__)


@command(Command.EXPAND_GOLD, Command.EXPAND_CASH)
def handle(ctx: CommandContext) -> None:
    expansion_id = int(ctx.args[0])

    prices_list = ctx.game_config.get("expansion_prices", [])
    current_idx = len(ctx.map.get("expansions", []))

    if current_idx >= len(prices_list):
        logger.warning("No more prices defined in expansion_prices for expansion number %s", current_idx + 1)
        return

    price_data = prices_list[current_idx]

    if ctx.cmd == Command.EXPAND_GOLD:
        cost = int(price_data.get("coins", 0))
        resource = Resource.GOLD
    else:
        cost = int(price_data.get("cash", 0))
        resource = Resource.CASH

    if ctx.info[resource] < cost:
        logger.warning("Not enough %s: needs %s, has %s", resource.value, cost, ctx.info[resource])
        return

    ctx.info[resource] -= cost

    if expansion_id in ctx.map["expansions"]:
        logger.warning("Expansion %s was already purchased", expansion_id)
        return

    ctx.map["expansions"].append(expansion_id)
    logger.info(
        "Expansion %s unlocked (price index %s), cost: %s %s",
        expansion_id, current_idx, cost, resource.value,
    )
