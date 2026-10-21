import logging
import time

from src.commands.base import CommandContext, command
from src.commands.validation import reject
from src.enums import Command, Resource

logger = logging.getLogger(__name__)

DEFAULT_COLLECT_MINUTES = [0.5, 5, 30, 120, 360, 720, 1440, 2160, 2880]


@command(Command.SPEED_COLLECT)
def handle(ctx: CommandContext) -> None:
    unique_id = ctx.iso_arg(0)
    # args[1] (speed type) is sent by the client but not needed.

    item_data = ctx.map_item(unique_id)
    props = item_data[6] if len(item_data) > 6 and isinstance(item_data[6], dict) else {}

    if "cp" not in props:
        reject(f"object {unique_id} has no active crop ('cp')")

    crop_id = int(props["cp"])

    globals_config = ctx.game_config.get("globals", {})
    collect_minutes = globals_config.get("COLLECT_MINUTES", {}).get("value", DEFAULT_COLLECT_MINUTES)

    if not 1 <= crop_id <= len(collect_minutes):
        reject(f"crop {crop_id} does not exist")

    duration_seconds = int(collect_minutes[crop_id - 1] * 60)

    start_time = int(item_data[3])
    current_ts = int(time.time())

    time_remaining = max(0, duration_seconds - (current_ts - start_time))
    gems_cost = max(1, (time_remaining + 3599) // 3600)

    ctx.pay(cash=gems_cost)
    item_data[3] = current_ts - duration_seconds

    logger.info("Sped up farm %s: cost %s gems, skipped %ss", unique_id, gems_cost, time_remaining)
    logger.info("Remaining gems: %s", ctx.info[Resource.CASH])
