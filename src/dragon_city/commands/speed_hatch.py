import logging
import time

from dragon_city.commands.base import CommandContext, command
from dragon_city.enums import Command, Resource

logger = logging.getLogger(__name__)


@command(Command.SPEED_HATCH)
def handle(ctx: CommandContext) -> None:
    egg_data = ctx.find_egg(ctx.uid_arg(0, "egg uid"))
    dragon_conf = ctx.item_config(egg_data.get("type"))

    hatching_time = dragon_conf.get("hatching_time", 0)
    start_time = int(egg_data.get("ts", 0))
    current_ts = int(time.time())

    time_remaining = max(0, hatching_time - (current_ts - start_time))
    gems_cost = max(1, (time_remaining + 3599) // 3600)

    ctx.pay(cash=gems_cost)
    egg_data["ts"] = current_ts - hatching_time

    logger.info("Sped up egg %s (type %s): cost %s gems", egg_data.get("id"), egg_data.get("type"), gems_cost)
    logger.info("Remaining gems: %s", ctx.info[Resource.CASH])
