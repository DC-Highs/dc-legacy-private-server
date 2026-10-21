import logging

from src.commands.base import CommandContext, command
from src.commands.validation import reject
from src.enums import Command, Resource

logger = logging.getLogger(__name__)

MAX_EXPANSION_ID = 9999


@command(Command.EXPAND_GOLD, Command.EXPAND_CASH)
def handle(ctx: CommandContext) -> None:
    expansion_id = ctx.int_arg(0, "expansion id", 0, MAX_EXPANSION_ID)

    prices_list = ctx.game_config.get("expansion_prices", [])
    expansions = ctx.map.setdefault("expansions", [])
    current_idx = len(expansions)

    if current_idx >= len(prices_list):
        reject(f"no more prices defined in expansion_prices for expansion number {current_idx + 1}")
    if expansion_id in expansions:
        reject(f"expansion {expansion_id} was already purchased")

    price_data = prices_list[current_idx]

    if ctx.cmd == Command.EXPAND_GOLD:
        cost = int(price_data.get("coins", 0))
        resource = Resource.GOLD
    else:
        cost = int(price_data.get("cash", 0))
        resource = Resource.CASH

    ctx.pay(**{resource.value: cost})

    expansions.append(expansion_id)
    logger.info(
        "Expansion %s unlocked (price index %s), cost: %s %s",
        expansion_id, current_idx, cost, resource.value,
    )
