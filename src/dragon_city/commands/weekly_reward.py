import json
import logging
import random
import time

from dragon_city.commands.base import CommandContext, command
from dragon_city.commands.validation import check_json_depth, reject, to_int
from dragon_city.enums import Command, Resource

logger = logging.getLogger(__name__)

FALLBACK_DRAGON_ID = 1011
# The bonus is weekly; a little under a week allows for clock differences.
MIN_SECONDS_BETWEEN_REWARDS = 5 * 86400

RESOURCE_BY_REWARD_TYPE = {
    "g": (Resource.GOLD, "gold"),
    "c": (Resource.CASH, "gems"),
    "f": (Resource.FOOD, "food"),
}
DRAGON_REWARD_TYPE = "u"


@command(Command.WEEKLY_REWARD)
def handle(ctx: CommandContext) -> None:
    raw = ctx.text_arg(0, "reward choice", 64)
    try:
        reward_args = json.loads(raw, parse_constant=lambda _c: reject("reward choice has an invalid number"))
    except ValueError:
        reject("reward choice is not valid JSON")
    if not isinstance(reward_args, list) or not 1 <= len(reward_args) <= 2:
        reject("reward choice must be a list of one or two numbers")
    check_json_depth(reward_args, "reward choice", max_depth=1, max_items=3)
    reward_index = to_int(reward_args[0], "reward index", 0, 100)
    dragon_index = to_int(reward_args[1], "dragon index", 0, 100) if len(reward_args) > 1 else 0

    now = int(time.time())
    last_claim = int(ctx.private_state.get("timeStampMondayBonus") or 0)
    if now - last_claim < MIN_SECONDS_BETWEEN_REWARDS:
        reject("the weekly reward was already claimed")

    globals_config = ctx.game_config.get("globals", {})
    monday_rewards = globals_config.get("MONDAY_BONUS_REWARDS", {}).get("value", [])
    monday_dragons = globals_config.get("MONDAY_BONUS_REWARDS_DRAGONS", {}).get("value", [])

    if reward_index >= len(monday_rewards):
        reject(f"reward index {reward_index} does not exist in the global config")

    reward = monday_rewards[reward_index]
    r_type = reward.get("type")
    r_value = reward.get("value", 0)

    if r_type in RESOURCE_BY_REWARD_TYPE:
        resource, label = RESOURCE_BY_REWARD_TYPE[r_type]
        ctx.info[resource] += r_value
        logger.info("Reward delivered: %s %s", r_value, label)
    elif r_type == DRAGON_REWARD_TYPE:
        dragon_id = monday_dragons[dragon_index] if dragon_index < len(monday_dragons) else FALLBACK_DRAGON_ID

        new_egg_uid = now + random.randint(1000, 9999)
        ctx.map["eggs"].append({
            "id": new_egg_uid,
            "type": dragon_id,
            "name": "Bonus",
            "xp": 0,
            "hatched": False,
            "ts": now,
        })
        logger.info("Reward delivered: egg of dragon %s", dragon_id)

    ctx.private_state["timeStampMondayBonus"] = now

    logger.info("timeStampMondayBonus updated to %s", now)
