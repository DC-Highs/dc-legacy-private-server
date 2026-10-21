import logging
import random

from dragon_city.commands.base import CommandContext, command
from dragon_city.commands.validation import reject
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
    new_level = ctx.int_arg(0, "level", 2, 1000)

    # One level at a time: skipping or repeating a level would pay its reward again.
    current_level = ctx.info.get("level", 1)
    if new_level != current_level + 1:
        reject(f"cannot go from level {current_level} to level {new_level}")

    levels_config = ctx.game_config.get("levels", [])
    level_info = levels_config[new_level - 1] if 0 <= new_level - 1 < len(levels_config) else None

    # The experience has to be there: the server tracks it from the commands it applied.
    if level_info is not None and ctx.info[Resource.XP] < level_info.get("xp_required", 0):
        reject(f"level {new_level} needs {level_info['xp_required']} xp, the player has {ctx.info[Resource.XP]}")

    ctx.info["level"] = new_level

    if level_info is not None:
        reward = level_info.get("reward", {})

        for reward_type, reward_amount in reward.items():
            if reward_type in REWARD_KEYS:
                ctx.info[REWARD_KEYS[reward_type]] += reward_amount

    if new_level >= BLACK_MARKET_UNLOCK_LEVEL and ctx.private_state.get("BlackMarketTs", 0) == 0:
        delay = random.randint(*BLACK_MARKET_FIRST_DELAY_RANGE)
        schedule_black_market(ctx.private_state, ctx.game_config, ctx.server_ts, delay)

        logger.info("Black market unlocked at level %s", BLACK_MARKET_UNLOCK_LEVEL)
