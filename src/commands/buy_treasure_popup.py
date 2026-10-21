import logging

from src.commands.base import CommandContext, command
from src.commands.validation import reject
from src.enums import Command, Resource

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
    treasure_id = ctx.int_arg(0, "treasure id", 0, 100000)

    if treasure_id not in TREASURES:
        reject(f"treasure id {treasure_id} is not registered on the server")

    resource, amount, price = TREASURES[treasure_id]

    ctx.pay(cash=price)
    ctx.info[resource] += amount

    logger.info("Bought treasure %s: +%s %s for -%s gems", treasure_id, amount, resource.value, price)
