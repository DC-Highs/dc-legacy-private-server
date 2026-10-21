import logging

from dragon_city.commands.base import CommandContext, command
from dragon_city.commands.validation import reject
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
    dragon = ctx.find_dragon(ctx.uid_arg(0, "dragon uid"))

    current_xp = dragon.get("xp", 0)
    current_level = (current_xp // 4) + 1

    if current_level >= len(FOOD_COSTS):
        reject(f"dragon {dragon.get('id')} already reached the highest registered level")

    food_cost = FOOD_COSTS[current_level]
    ctx.pay(food=food_cost)

    dragon["xp"] = current_xp + 1
    new_level = (dragon["xp"] // 4) + 1

    dragon_type_str = str(dragon.get("type"))
    owned = ctx.map["ownedDragons"]

    if dragon_type_str not in owned:
        owned[dragon_type_str] = [1, 0, 0]

    if new_level >= 4:
        owned[dragon_type_str][1] = 2
    if new_level >= 7:
        owned[dragon_type_str][2] = 3

    logger.info("Fed dragon '%s' (uid %s)", dragon.get("name", "Unknown"), dragon.get("id"))
    logger.info("Dragon xp is now %s | cost: %s | remaining food: %s", dragon["xp"], food_cost, ctx.info[Resource.FOOD])
