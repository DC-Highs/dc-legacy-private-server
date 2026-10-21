import logging

from src.commands.base import CommandContext, command
from src.commands.validation import reject
from src.enums import Command, Resource

logger = logging.getLogger(__name__)

# Short resource codes used by the game config -> playerInfo keys.
RESOURCE_BY_CODE = {"g": Resource.GOLD.value, "f": Resource.FOOD.value}


@command(Command.BUY_TREASURE_NEW)
def handle(ctx: CommandContext) -> None:
    treasure_id = str(ctx.int_arg(0, "treasure id", 0, 100000))

    treasures = ctx.game_config.get("treasure_items")
    if not treasures or treasure_id not in treasures:
        reject(f"treasure {treasure_id} not found in the config (treasure_items)")

    treasure_data = treasures[treasure_id]

    price = int(treasure_data.get("price", 0))
    amount = int(treasure_data.get("amount", 0))
    res_type = treasure_data.get("type", "")
    res_type = RESOURCE_BY_CODE.get(res_type, res_type)
    if res_type not in (Resource.GOLD.value, Resource.FOOD.value):
        reject(f"treasure {treasure_id} has an unsupported resource type {res_type!r}")

    ctx.pay(cash=price)
    ctx.info[res_type] = ctx.info.get(res_type, 0) + amount

    logger.info("Bought treasure %s", treasure_id)
    logger.info("Cost: %s gems | reward: +%s %s", price, amount, res_type)
    logger.info("Remaining gems: %s", ctx.info[Resource.CASH])
