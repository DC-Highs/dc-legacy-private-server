import logging
import random
import time

from dragon_city.commands.base import CommandContext, command
from dragon_city.enums import Command, Resource
from dragon_city.game.items import get_item_config
from dragon_city.names import DRAGON_NAMES

logger = logging.getLogger(__name__)


@command(Command.BUY_EGG)
def handle(ctx: CommandContext) -> None:
    egg_uid = ctx.args[0]
    dragon_id = ctx.args[1]

    item_cfg = get_item_config(ctx.game_config, dragon_id)
    if not item_cfg:
        logger.warning("Dragon %s does not exist in the game config", dragon_id)
        return

    info = ctx.info
    costs = item_cfg.get("costs", {})
    gold_cost = costs.get("g", 0)
    cash_cost = costs.get("c", 0)

    if gold_cost > 0:
        info[Resource.GOLD] = max(0, info[Resource.GOLD] - gold_cost)
    if cash_cost > 0:
        info[Resource.CASH] = max(0, info[Resource.CASH] - cash_cost)

    info[Resource.XP] += item_cfg.get("xp", 0)

    if "eggs" not in ctx.map:
        ctx.map["eggs"] = []

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
