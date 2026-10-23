"""Hatching a "Mistery Egg" (items 154-157 in the game config): instead of its own species,

it rolls a random reward from its tier's weighted table (``mistery_egg`` in the game config),
same spelling the config itself uses. The roll happens entirely on the server; the client has
no say in which reward is picked.
"""
import logging
import random

from src.commands.base import CommandContext, command
from src.commands.validation import reject
from src.enums import Command, Resource

logger = logging.getLogger(__name__)

MISTERY_EGG_GROUP = "MISTERY_EGG"


def _tier_of(item_cfg: dict) -> str:
    """"Small/Medium/Large/Super Mistery Egg" -> "SMALL"/"MEDIUM"/"LARGE"/"SUPER"."""
    name = str(item_cfg.get("name", ""))
    return name.split(" ", 1)[0].upper()


@command(Command.MISTERY_EGG_HATCH)
def handle(ctx: CommandContext) -> None:
    egg_uid = ctx.uid_arg(0, "egg uid")
    egg_data = ctx.find_egg(egg_uid)
    item_cfg = ctx.item_config(egg_data.get("type"))

    if item_cfg.get("group_type") != MISTERY_EGG_GROUP:
        reject(f"egg {egg_uid} is not a mystery egg")

    tier = _tier_of(item_cfg)
    tier_cfg = ctx.game_config.get("mistery_egg", {}).get(tier)
    rewards = tier_cfg.get("rewards") if tier_cfg else None
    chances = tier_cfg.get("chances") if tier_cfg else None

    # The reward table lives in the game config, not in the client: a malformed or missing
    # table is refused rather than guessed at.
    if not rewards or not chances or len(rewards) != len(chances) or sum(chances) <= 0:
        reject(f"mystery egg tier {tier} has no reward table in the game config")

    reward = random.choices(rewards, weights=chances, k=1)[0]

    ctx.map["eggs"].remove(egg_data)

    if isinstance(reward, dict):
        info = ctx.info
        gold_reward = reward.get("g", 0)
        food_reward = reward.get("f", 0)
        cash_reward = reward.get("c", 0)
        info[Resource.GOLD] += gold_reward
        info[Resource.FOOD] += food_reward
        info[Resource.CASH] += cash_reward
        logger.info(
            "Mystery egg (%s) hatched: gold +%s | food +%s | gems +%s",
            tier, gold_reward, food_reward, cash_reward,
        )
    else:
        # A plain number in the table is a dragon type id: stored unhatched, like a Deus
        # card prize or a kompu box prize, placed later with place_stored_dragon.
        dragon_id = reward
        ctx.map["store"]["dragons"].append({"iid": dragon_id, "lvl": 0})
        logger.info("Mystery egg (%s) hatched: dragon %s stored in the warehouse", tier, dragon_id)
