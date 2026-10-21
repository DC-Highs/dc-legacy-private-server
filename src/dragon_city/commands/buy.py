import logging

from dragon_city.commands.base import CommandContext, command
from dragon_city.enums import Command, GroupType, Resource
from dragon_city.game.items import get_item_config

logger = logging.getLogger(__name__)


@command(Command.BUY)
def handle(ctx: CommandContext) -> None:
    iso_id = str(ctx.args[0])
    item_id = ctx.args[1]
    tx = ctx.args[2]
    ty = ctx.args[3]
    p_id = ctx.args[4]
    frame = ctx.args[5]
    flag = ctx.args[6]

    item_cfg = get_item_config(ctx.game_config, item_id)
    if not item_cfg:
        logger.warning("Item %s does not exist in the game config", item_id)
        return

    info = ctx.info
    group_type = item_cfg.get("group_type", "")
    costs = item_cfg.get("costs", {})
    gold_cost = costs.get("g", 0)
    cash_cost = costs.get("c", 0)

    if gold_cost > 0:
        info[Resource.GOLD] = max(0, info[Resource.GOLD] - gold_cost)
    if cash_cost > 0:
        info[Resource.CASH] = max(0, info[Resource.CASH] - cash_cost)

    build_time = item_cfg.get("build_time", 0)
    attributes = {}
    current_ts = ctx.server_ts

    if group_type == GroupType.HABITAT:
        attributes["ar"] = 0
        attributes["lat"] = current_ts

    if build_time > 0:
        attributes["tb"] = current_ts + build_time
    else:
        info[Resource.XP] += item_cfg.get("xp", 0)

    ctx.map["items"][iso_id] = [item_id, tx, ty, p_id, frame, flag, attributes]

    logger.info("Built %s at (%s, %s) with attributes %s", item_cfg.get("name"), tx, ty, attributes)
    logger.info(
        "Remaining gold: %s | cash: %s | xp: %s",
        info[Resource.GOLD], info[Resource.CASH], info[Resource.XP],
    )
