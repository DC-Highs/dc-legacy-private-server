import json
import logging
import random
import time

from dragon_city.commands.base import CommandContext, command
from dragon_city.enums import Command, Resource

logger = logging.getLogger(__name__)

FALLBACK_DRAGON_ID = 1011

RESOURCE_BY_REWARD_TYPE = {
    "g": (Resource.GOLD, "gold"),
    "c": (Resource.CASH, "gems"),
    "f": (Resource.FOOD, "food"),
}
DRAGON_REWARD_TYPE = "u"


@command(Command.WEEKLY_REWARD)
def handle(ctx: CommandContext) -> None:
    reward_args = json.loads(ctx.args[0])
    reward_index = int(reward_args[0])
    dragon_index = int(reward_args[1]) if len(reward_args) > 1 else 0

    globals_config = ctx.game_config.get("globals", {})
    monday_rewards = globals_config.get("MONDAY_BONUS_REWARDS", {}).get("value", [])
    monday_dragons = globals_config.get("MONDAY_BONUS_REWARDS_DRAGONS", {}).get("value", [])

    if reward_index >= len(monday_rewards):
        logger.warning("Reward index %s does not exist in the global config", reward_index)
        return

    reward = monday_rewards[reward_index]
    r_type = reward.get("type")
    r_value = reward.get("value", 0)

    if r_type in RESOURCE_BY_REWARD_TYPE:
        resource, label = RESOURCE_BY_REWARD_TYPE[r_type]
        ctx.info[resource] += r_value
        logger.info("Reward delivered: %s %s", r_value, label)
    elif r_type == DRAGON_REWARD_TYPE:
        dragon_id = monday_dragons[dragon_index] if dragon_index < len(monday_dragons) else FALLBACK_DRAGON_ID

        new_egg_uid = int(time.time()) + random.randint(1000, 9999)
        if "eggs" not in ctx.map:
            ctx.map["eggs"] = []
        ctx.map["eggs"].append({
            "id": new_egg_uid,
            "type": dragon_id,
            "name": "Bonus",
            "xp": 0,
            "hatched": False,
            "ts": int(time.time()),
        })
        logger.info("Reward delivered: egg of dragon %s", dragon_id)

    if "privateState" not in ctx.player_data:
        ctx.player_data["privateState"] = {}

    current_ts = int(time.time())
    ctx.private_state["timeStampMondayBonus"] = current_ts

    logger.info("timeStampMondayBonus updated to %s", current_ts)
