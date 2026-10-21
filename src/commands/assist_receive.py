import logging

from src.commands.base import CommandContext, command
from src.commands.validation import reject
from src.enums import Command, GroupType, Resource
from src.game.items import get_item_config

logger = logging.getLogger(__name__)

REWARD_XP = 10
HABITAT_REWARD_GOLD = 10
FARM_REWARD_FOOD = 10


@command(Command.ASSIST_RECEIVE)
def handle(ctx: CommandContext) -> None:
    item_type_id = ctx.int_arg(0, "item type", 1)

    # Each reward corresponds to one click a neighbour really sent (see assist_neighbor).
    rewards_left = ctx.private_state.get("assistRewardsLeft", 0)
    if not isinstance(rewards_left, int) or rewards_left <= 0:
        reject("there are no neighbour assists to collect")
    ctx.private_state["assistRewardsLeft"] = rewards_left - 1

    item_cfg = get_item_config(ctx.game_config, item_type_id)
    group_type = item_cfg.get("group_type", "") if item_cfg else None

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
