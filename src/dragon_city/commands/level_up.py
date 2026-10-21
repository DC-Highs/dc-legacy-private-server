import logging
import random

from dragon_city.commands.base import CommandContext, command
from dragon_city.enums import Command, Resource
from dragon_city.game.black_market import schedule_black_market

logger = logging.getLogger(__name__)

BLACK_MARKET_UNLOCK_LEVEL = 5
BLACK_MARKET_FIRST_DELAY_RANGE = (86400, 259200)

REWARD_KEYS = {
    "c": Resource.CASH,
    "g": Resource.GOLD,
    "f": Resource.FOOD,
    "x": Resource.XP,
}


@command(Command.LEVEL_UP)
def handle(ctx: CommandContext) -> None:
    new_level = int(ctx.args[0])

    ctx.info["level"] = new_level

    levels_config = ctx.game_config.get("levels", [])

    if 0 <= new_level - 1 < len(levels_config):
        reward = levels_config[new_level - 1].get("reward", {})

        for reward_type, reward_amount in reward.items():
            if reward_type in REWARD_KEYS:
                ctx.info[REWARD_KEYS[reward_type]] += reward_amount

    if new_level >= BLACK_MARKET_UNLOCK_LEVEL and ctx.private_state.get("BlackMarketTs", 0) == 0:
        delay = random.randint(*BLACK_MARKET_FIRST_DELAY_RANGE)
        schedule_black_market(ctx.private_state, ctx.game_config, ctx.server_ts, delay)

        logger.info("Black market unlocked at level %s", BLACK_MARKET_UNLOCK_LEVEL)
