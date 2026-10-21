import logging

from dragon_city.commands.base import CommandContext, command
from dragon_city.commands.validation import reject
from dragon_city.enums import Command, Resource

logger = logging.getLogger(__name__)

MAX_EXPANSION_ID = 9999


@command(Command.EXPAND_ISLAND)
def handle(ctx: CommandContext) -> None:
    expansion_id = ctx.int_arg(0, "expansion id", 0, MAX_EXPANSION_ID)
    cost_index = ctx.int_arg(1, "cost index", 0, 1000)

    expansions = ctx.map.setdefault("expansions", [])
    if expansion_id in expansions:
        reject(f"expansion {expansion_id} was already purchased")

    islands_costs = ctx.game_config.get("globals", {}).get("ISLANDS_COSTS", {}).get("value", [])
    if cost_index >= len(islands_costs):
        reject(f"cost index {cost_index} exceeds the ISLANDS_COSTS limit")

    cost_item = islands_costs[cost_index]
    cost_obj = cost_item.get("value", cost_item) if isinstance(cost_item, dict) else {}

    ctx.pay(gold=int(cost_obj.get("g", 0)), cash=int(cost_obj.get("c", 0)))
    expansions.append(expansion_id)

    logger.info("Island expanded to plot %s", expansion_id)
    logger.info("Cost charged (index %s): %s", cost_index, cost_obj)
    logger.debug("Gold %s | gems %s", ctx.info[Resource.GOLD], ctx.info[Resource.CASH])
