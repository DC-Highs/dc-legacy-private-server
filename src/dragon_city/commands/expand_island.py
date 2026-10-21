import logging

from dragon_city.commands.base import CommandContext, command
from dragon_city.enums import Command, Resource

logger = logging.getLogger(__name__)


@command(Command.EXPAND_ISLAND)
def handle(ctx: CommandContext) -> None:
    expansion_id = int(ctx.args[0])
    cost_index = int(ctx.args[1])

    if "expansions" not in ctx.map:
        ctx.map["expansions"] = []

    if expansion_id not in ctx.map["expansions"]:
        ctx.map["expansions"].append(expansion_id)

    try:
        islands_costs = ctx.game_config.get("globals", {}).get("ISLANDS_COSTS", {}).get("value", [])

        if cost_index >= len(islands_costs):
            logger.warning("Cost index %s exceeds the ISLANDS_COSTS limit", cost_index)
            return

        cost_item = islands_costs[cost_index]
        cost_obj = cost_item.get("value", cost_item) if isinstance(cost_item, dict) else {}

        for res_type, amount in cost_obj.items():
            amt = int(amount)
            if res_type == "g":
                ctx.info[Resource.GOLD] = max(0, ctx.info[Resource.GOLD] - amt)
            elif res_type == "c":
                ctx.info[Resource.CASH] = max(0, ctx.info[Resource.CASH] - amt)

        logger.info("Island expanded to plot %s", expansion_id)
        logger.info("Cost charged (index %s): %s", cost_index, cost_obj)

    except Exception:
        logger.exception("Failed to charge the cost of expand_island")
