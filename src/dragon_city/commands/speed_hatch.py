import logging
import time

from dragon_city.commands.base import CommandContext, command
from dragon_city.enums import Command, Resource

logger = logging.getLogger(__name__)


@command(Command.SPEED_HATCH)
def handle(ctx: CommandContext) -> None:
    egg_id = ctx.args[0]

    if "eggs" not in ctx.player_data.get("map", {}):
        return

    egg_data = next((egg for egg in ctx.map["eggs"] if egg.get("id") == egg_id), None)
    if not egg_data:
        logger.warning("Egg with id %s not found on the map", egg_id)
        return

    dragon_type = str(egg_data.get("type"))

    all_items = ctx.game_config.get("items", [])
    if isinstance(all_items, dict):
        dragon_conf = all_items.get(dragon_type)
    else:
        dragon_conf = next((i for i in all_items if str(i.get("id")) == dragon_type), None)

    if not dragon_conf:
        logger.warning("No config found for dragon type %s", dragon_type)
        return

    hatching_time = dragon_conf.get("hatching_time", 0)
    start_time = int(egg_data.get("ts", 0))
    current_ts = int(time.time())

    time_remaining = max(0, hatching_time - (current_ts - start_time))
    gems_cost = max(1, (time_remaining + 3599) // 3600)

    if ctx.info[Resource.CASH] < gems_cost:
        logger.warning("Not enough gems for speed_hatch on egg %s", egg_id)
        return

    ctx.info[Resource.CASH] -= gems_cost
    egg_data["ts"] = current_ts - hatching_time

    logger.info("Sped up egg %s (type %s): cost %s gems", egg_id, dragon_type, gems_cost)
    logger.info("Remaining gems: %s", ctx.info[Resource.CASH])
