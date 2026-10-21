import logging

from dragon_city.commands.base import CommandContext, command
from dragon_city.enums import Command, GroupType, Resource

logger = logging.getLogger(__name__)

REWARD_XP = 10
HABITAT_REWARD_GOLD = 10
FARM_REWARD_FOOD = 10


@command(Command.ASSIST_RECEIVE)
def handle(ctx: CommandContext) -> None:
    item_type_id = int(ctx.args[0])

    group_type = None
    for item in ctx.game_config.get("items", []):
        if item.get("id") == item_type_id:
            group_type = item.get("group_type", "")
            break

    reward_gold = 0
    reward_food = 0

    if group_type == GroupType.HABITAT:
        reward_gold = HABITAT_REWARD_GOLD
    elif group_type == GroupType.FARM:
        reward_food = FARM_REWARD_FOOD

    info = ctx.info
    info[Resource.XP] += REWARD_XP
    info[Resource.GOLD] += reward_gold
    info[Resource.FOOD] += reward_food

    logger.info("Resource assist received")
    logger.info(
        "Current resources: food %s | gold %s | xp %s",
        info[Resource.FOOD], info[Resource.GOLD], info[Resource.XP],
    )
