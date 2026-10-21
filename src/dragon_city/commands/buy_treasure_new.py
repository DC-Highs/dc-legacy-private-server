import logging

from dragon_city.commands.base import CommandContext, command
from dragon_city.enums import Command, Resource

logger = logging.getLogger(__name__)

# Short resource codes used by the game config -> playerInfo keys.
RESOURCE_BY_CODE = {"g": Resource.GOLD.value, "f": Resource.FOOD.value}


@command(Command.BUY_TREASURE_NEW)
def handle(ctx: CommandContext) -> None:
    treasure_id = str(ctx.args[0])

    treasures = ctx.game_config.get("treasure_items")
    if not treasures or treasure_id not in treasures:
        logger.warning("Treasure %s not found in the config (treasure_items)", treasure_id)
        return

    treasure_data = treasures[treasure_id]

    price = int(treasure_data.get("price", 0))
    amount = int(treasure_data.get("amount", 0))
    res_type = treasure_data.get("type", "")
    res_type = RESOURCE_BY_CODE.get(res_type, res_type)

    info = ctx.info
    current_cash = int(info.get(Resource.CASH, 0))

    if current_cash < price:
        logger.warning("Not enough funds: %s gems available but treasure %s costs %s", current_cash, treasure_id, price)
        return

    info[Resource.CASH] -= price

    if res_type in info:
        info[res_type] += amount
    else:
        info[res_type] = amount

    logger.info("Bought treasure %s", treasure_id)
    logger.info("Cost: %s gems | reward: +%s %s", price, amount, res_type)
    logger.info("Remaining gems: %s", info[Resource.CASH])
