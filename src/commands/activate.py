import logging
import time

from src.commands.base import CommandContext, command
from src.commands.validation import reject
from src.enums import Command, GroupType

logger = logging.getLogger(__name__)


@command(Command.ACTIVATE)
def handle(ctx: CommandContext) -> None:
    iso_id = ctx.iso_arg(0)
    cp_val = ctx.int_arg(1, "crop", 0, 1000)

    item_data = ctx.map_item(iso_id)
    item_cfg = ctx.item_config(item_data[0])

    while len(item_data) < 7:
        item_data.append({})
    if not isinstance(item_data[6], dict):
        item_data[6] = {}
    attrs = item_data[6]

    group_type = item_cfg.get("group_type", "")
    properties = item_cfg.get("properties", {})

    if group_type == GroupType.FARM or "multiCollectable" in properties:
        if cp_val > 0:
            collect_prices = ctx.game_config.get("globals", {}).get("COLLECT_PRICE", {}).get("value", [])

            if cp_val > len(collect_prices):
                reject(f"crop {cp_val} does not exist")

            cost = collect_prices[cp_val - 1]
            ctx.pay(gold=cost.get("g", 0), cash=cost.get("c", 0))

            attrs["cp"] = cp_val
            item_data[3] = int(time.time())
        else:
            attrs["cp"] = 0
            item_data[3] = 0

    elif group_type == GroupType.OBSTACLE:
        costs = item_cfg.get("costs", {})
        ctx.pay(gold=costs.get("g", 0), cash=costs.get("c", 0))

        item_data[3] = int(time.time())

    logger.info("Activated object %s with start timestamp %s", iso_id, item_data[3])
