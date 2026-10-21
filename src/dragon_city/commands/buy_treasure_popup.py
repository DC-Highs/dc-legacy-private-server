import logging

from dragon_city.commands.base import CommandContext, command
from dragon_city.enums import Command, Resource

logger = logging.getLogger(__name__)

# Treasure id -> (resource, amount, price in gems)
TREASURES = {
    1: (Resource.GOLD, 75000, 15),
    2: (Resource.GOLD, 200000, 30),
    3: (Resource.GOLD, 500000, 80),
    5: (Resource.FOOD, 10000, 15),
    6: (Resource.FOOD, 22500, 30),
    7: (Resource.FOOD, 70000, 80),
}


@command(Command.BUY_TREASURE_POPUP)
def handle(ctx: CommandContext) -> None:
    treasure_id = int(ctx.args[0])

    if treasure_id not in TREASURES:
        logger.warning("Treasure id %s is not registered on the server", treasure_id)
        return

    resource, amount, price = TREASURES[treasure_id]
    info = ctx.info

    if info[Resource.CASH] < price:
        logger.warning("Not enough gems for treasure %s, current gems: %s", treasure_id, info[Resource.CASH])
        return

    info[Resource.CASH] -= price
    info[resource] += amount

    logger.info("Bought treasure %s: +%s %s for -%s gems", treasure_id, amount, resource.value, price)
