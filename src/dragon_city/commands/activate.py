import logging
import time

from dragon_city.commands.base import CommandContext, command
from dragon_city.enums import Command, GroupType, Resource
from dragon_city.game.items import get_item_config

logger = logging.getLogger(__name__)


@command(Command.ACTIVATE)
def handle(ctx: CommandContext) -> None:
    iso_id = str(ctx.args[0])
    cp_val = ctx.args[1]

    if iso_id not in ctx.map["items"]:
        return

    info = ctx.info
    item_data = ctx.map["items"][iso_id]
    item_id = item_data[0]

    while len(item_data) < 7:
        item_data.append({})

    attrs = item_data[6]

    item_cfg = get_item_config(ctx.game_config, item_id)

    if item_cfg:
        group_type = item_cfg.get("group_type", "")
        properties = item_cfg.get("properties", {})

        if group_type == GroupType.FARM or "multiCollectable" in properties:
            if isinstance(cp_val, int) and cp_val > 0:
                collect_prices = ctx.game_config.get("globals", {}).get("COLLECT_PRICE", {}).get("value", [])

                if (cp_val - 1) < len(collect_prices):
                    cost = collect_prices[cp_val - 1]
                    if "g" in cost:
                        info[Resource.GOLD] = max(0, info[Resource.GOLD] - cost["g"])
                    if "c" in cost:
                        info[Resource.CASH] = max(0, info[Resource.CASH] - cost["c"])

                attrs["cp"] = cp_val
                item_data[3] = int(time.time())

            elif cp_val == 0:
                attrs["cp"] = 0
                item_data[3] = 0

        elif group_type == GroupType.OBSTACLE:
            costs = item_cfg.get("costs", {})
            if "g" in costs:
                info[Resource.GOLD] = max(0, info[Resource.GOLD] - costs["g"])
            if "c" in costs:
                info[Resource.CASH] = max(0, info[Resource.CASH] - costs["c"])

            item_data[3] = int(time.time())

    logger.info("Activated object %s with start timestamp %s", iso_id, item_data[3])
