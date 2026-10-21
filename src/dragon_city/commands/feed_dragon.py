import logging

from dragon_city.commands.base import CommandContext, command
from dragon_city.enums import Command, Resource

logger = logging.getLogger(__name__)

# Food needed to raise a dragon, indexed by its current level.
FOOD_COSTS = (
    0, 5, 10, 20, 40, 80, 160, 320, 640, 1280,
    1664, 2163, 2812, 3656, 4753, 6178, 8032, 10441, 13574, 17646,
    22940, 29822, 38768, 50398, 65518, 88173, 110725, 143943, 187126, 243264,
    316243, 411115, 534450, 694785, 903220, 1174187, 1526443, 1984375, 2579688, 3353594,
    4359673,
)


@command(Command.FEED_DRAGON)
def handle(ctx: CommandContext) -> None:
    dragon_uid = ctx.args[0]

    for dragon in ctx.map.get("dragons", []):
        if str(dragon.get("id")) != str(dragon_uid):
            continue

        current_xp = dragon.get("xp", 0)
        current_level = (current_xp // 4) + 1

        if current_level >= len(FOOD_COSTS):
            logger.warning("Dragon %s already reached the highest registered level", dragon_uid)
            return

        food_cost = FOOD_COSTS[current_level]
        info = ctx.info

        if info[Resource.FOOD] < food_cost:
            logger.warning("Not enough food (%s required) to feed dragon %s", food_cost, dragon_uid)
            return

        info[Resource.FOOD] -= food_cost

        dragon["xp"] = current_xp + 1
        new_level = (dragon["xp"] // 4) + 1

        dragon_type_str = str(dragon.get("type"))

        if "ownedDragons" not in ctx.map:
            ctx.map["ownedDragons"] = {}

        if dragon_type_str not in ctx.map["ownedDragons"]:
            ctx.map["ownedDragons"][dragon_type_str] = [1, 0, 0]

        if new_level >= 4:
            ctx.map["ownedDragons"][dragon_type_str][1] = 2
        if new_level >= 7:
            ctx.map["ownedDragons"][dragon_type_str][2] = 3

        logger.info("Fed dragon '%s' (uid %s)", dragon.get("name", "Unknown"), dragon_uid)
        logger.info("Dragon xp is now %s | cost: %s | remaining food: %s", dragon["xp"], food_cost, info[Resource.FOOD])
        return

    logger.warning("Dragon with uid %s not found on the map", dragon_uid)
