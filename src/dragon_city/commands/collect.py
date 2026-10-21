import logging
import time

from dragon_city.commands.base import CommandContext, command
from dragon_city.enums import Command, Resource

logger = logging.getLogger(__name__)


@command(Command.COLLECT)
def handle(ctx: CommandContext) -> None:
    args = ctx.args
    iso_id = str(args[0])

    if iso_id not in ctx.map["items"]:
        logger.warning("Cannot collect: item %s does not exist on the map", iso_id)
        return

    info = ctx.info
    item_data = ctx.map["items"][iso_id]

    while len(item_data) <= 6:
        item_data.append({})
    if not isinstance(item_data[6], dict):
        item_data[6] = {}

    attrs = item_data[6]
    current_ts = int(time.time())

    if len(args) > 1 and isinstance(args[1], (int, float)):
        gold_collected = int(args[1])
        info[Resource.GOLD] += gold_collected

        item_data[3] = current_ts
        attrs["lat"] = current_ts

        logger.info("Collected habitat gold: %s", gold_collected)

    elif len(args) > 1 and args[1] == "fc":
        if "cp" in attrs:
            cp_index = int(attrs["cp"]) - 1

            globals_config = ctx.game_config.get("globals", {})
            collect_values = globals_config.get("COLLECT_VALUES", {}).get("value", [])
            collect_xp = globals_config.get("COLLECT_XP", {}).get("value", [])

            if 0 <= cp_index < len(collect_values):
                food_collected = int(collect_values[cp_index])
                xp_collected = int(collect_xp[cp_index])

                info[Resource.FOOD] += food_collected
                info[Resource.XP] += xp_collected

                logger.info("Collected farm food: %s | xp: %s", food_collected, xp_collected)

            del attrs["cp"]

        item_data[3] = 0

    else:
        item_data[3] = 0
        if "lat" in attrs:
            attrs["lat"] = current_ts
        logger.info("Collected from item %s", iso_id)

    logger.info(
        "Current state -> gold: %s | food: %s | xp: %s",
        info[Resource.GOLD], info[Resource.FOOD], info[Resource.XP],
    )
