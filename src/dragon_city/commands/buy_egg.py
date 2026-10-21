import logging
import random
import time

from dragon_city.commands.base import CommandContext, command
from dragon_city.commands.validation import reject
from dragon_city.enums import Command, GroupType, Resource
from dragon_city.names import DRAGON_NAMES

logger = logging.getLogger(__name__)


@command(Command.BUY_EGG)
def handle(ctx: CommandContext) -> None:
    egg_uid = ctx.new_uid(0, "egg uid")
    dragon_id = ctx.int_arg(1, "dragon id", 1)

    item_cfg = ctx.item_config(dragon_id)
    costs = item_cfg.get("costs")

    if item_cfg.get("group_type") != GroupType.DRAGON:
        reject(f"item {dragon_id} is not a dragon")
    if not costs:
        reject(f"dragon {dragon_id} is not for sale")

    ctx.pay(gold=costs.get("g", 0), cash=costs.get("c", 0), food=costs.get("f", 0))

    info = ctx.info
    info[Resource.XP] += item_cfg.get("xp", 0)

    ctx.map["eggs"].append({
        "id": egg_uid,
        "type": dragon_id,
        "name": random.choice(DRAGON_NAMES),
        "xp": 0,
        "hatched": False,
        "ts": int(time.time()),
    })

    logger.info("Bought egg of %s (uid %s)", item_cfg.get("name"), egg_uid)
    logger.info(
        "Gold: %s | cash: %s | xp: %s",
        info[Resource.GOLD], info[Resource.CASH], info[Resource.XP],
    )
