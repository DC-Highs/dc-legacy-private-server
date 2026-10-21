import logging

from dragon_city.commands.base import CommandContext, command
from dragon_city.commands.validation import MAX_COORDINATE, MAX_SMALL_INT, reject
from dragon_city.enums import Command, GroupType, Resource

logger = logging.getLogger(__name__)


@command(Command.BUY)
def handle(ctx: CommandContext) -> None:
    iso_id = ctx.iso_arg(0)
    item_id = ctx.int_arg(1, "item id", 1)
    tx = ctx.int_arg(2, "x", 0, MAX_COORDINATE)
    ty = ctx.int_arg(3, "y", 0, MAX_COORDINATE)
    p_id = ctx.int_arg(4, "parent id", 0, MAX_SMALL_INT)
    frame = ctx.int_arg(5, "frame", 0, MAX_SMALL_INT)
    flag = ctx.int_arg(6, "flag", 0, MAX_SMALL_INT)

    item_cfg = ctx.item_config(item_id)
    group_type = item_cfg.get("group_type", "")
    costs = item_cfg.get("costs")

    if group_type == GroupType.DRAGON:
        reject(f"item {item_id} is a dragon, eggs are bought with buy_egg")
    if not costs:
        reject(f"item {item_id} is not for sale")
    if iso_id in ctx.map["items"]:
        reject(f"iso id {iso_id} is already used by another object")
    if item_cfg.get("min_level", 1) > ctx.info.get("level", 1):
        reject(f"item {item_id} requires level {item_cfg['min_level']}")

    ctx.pay(gold=costs.get("g", 0), cash=costs.get("c", 0), food=costs.get("f", 0))

    info = ctx.info
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
