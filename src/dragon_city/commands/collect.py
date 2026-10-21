import logging
import time

from dragon_city.commands.base import CommandContext, command
from dragon_city.commands.validation import MAX_SAFE_INT, reject
from dragon_city.enums import Command, GroupType, Resource
from dragon_city.game.items import get_item_config

logger = logging.getLogger(__name__)

# The server does not simulate the exact gold formula, so it only bounds what a habitat
# could have produced: dragons' coins per minute, with a generous margin.
GOLD_TOLERANCE = 2.0
GOLD_MARGIN = 100
MAX_ACCRUAL_SECONDS = 7 * 86400
CROP_TIME_TOLERANCE = 5


def _habitat_gold_cap(ctx: CommandContext, iso_id: str, item_data: list, attrs: dict, now: int) -> int:
    rate_per_minute = 0
    for dragon in ctx.map["dragons"]:
        if str(dragon.get("habitatId")) != iso_id:
            continue
        dragon_cfg = get_item_config(ctx.game_config, dragon.get("type"))
        if not dragon_cfg:
            continue
        level = (dragon.get("xp", 0) // 4) + 1
        rate_per_minute += dragon_cfg.get("starting_coins", 0) + dragon_cfg.get("coins_added", 0) * (level - 1)

    last_collect = max(int(item_data[3] or 0), int(attrs.get("lat", 0) or 0))
    elapsed = min(MAX_ACCRUAL_SECONDS, max(0, now - last_collect)) if last_collect else MAX_ACCRUAL_SECONDS
    return int(rate_per_minute * (elapsed / 60.0) * GOLD_TOLERANCE) + GOLD_MARGIN


def _allow_tutorial_harvest_once(ctx: CommandContext, iso_id: str) -> None:
    """The tutorial replays plant and harvest in one packet, so its first harvest cannot wait."""
    in_tutorial = str(ctx.info.get("completed_tutorial", 0)) in ("0", "")
    if not in_tutorial or ctx.private_state.get("tutorialCropHarvested"):
        reject(f"the crop on farm {iso_id} is not ready yet")
    ctx.private_state["tutorialCropHarvested"] = True


@command(Command.COLLECT)
def handle(ctx: CommandContext) -> None:
    args = ctx.args
    iso_id = ctx.iso_arg(0)

    info = ctx.info
    item_data = ctx.map_item(iso_id)

    while len(item_data) <= 6:
        item_data.append({})
    if not isinstance(item_data[6], dict):
        item_data[6] = {}

    attrs = item_data[6]
    current_ts = int(time.time())
    item_cfg = get_item_config(ctx.game_config, item_data[0]) or {}

    if len(args) > 1 and isinstance(args[1], (int, float)) and not isinstance(args[1], bool):
        if item_cfg.get("group_type") != GroupType.HABITAT:
            reject(f"object {iso_id} is not a habitat")
        claimed = ctx.int_arg(1, "gold collected", 0, MAX_SAFE_INT)
        cap = _habitat_gold_cap(ctx, iso_id, item_data, attrs, current_ts)
        gold_collected = min(claimed, cap)
        if gold_collected < claimed:
            logger.warning(
                "Player %s claimed %s gold from habitat %s but at most %s was produced",
                ctx.user_id, claimed, iso_id, cap,
            )
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
            collect_minutes = globals_config.get("COLLECT_MINUTES", {}).get("value", [])

            if 0 <= cp_index < len(collect_values):
                # A crop can only be harvested once it has grown (speed_collect moves the start back).
                if cp_index < len(collect_minutes):
                    grown_for = current_ts - int(item_data[3] or 0)
                    if grown_for + CROP_TIME_TOLERANCE < int(collect_minutes[cp_index] * 60):
                        _allow_tutorial_harvest_once(ctx, iso_id)

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
