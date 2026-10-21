import logging

from dragon_city.commands.base import CommandContext, command
from dragon_city.commands.validation import reject
from dragon_city.enums import Command, Resource
from dragon_city.game.items import get_item_config

logger = logging.getLogger(__name__)


@command(Command.FINISH_BUILDING)
def handle(ctx: CommandContext) -> None:
    iso_id = ctx.iso_arg(0)
    is_speed_up = ctx.int_arg(1, "speed up flag", 0, 1000)

    item_data = ctx.map_item(iso_id)

    # Only objects still under construction can be finished; otherwise the client could
    # call this repeatedly to collect the build experience over and over.
    if len(item_data) <= 6 or not isinstance(item_data[6], dict) or "tb" not in item_data[6]:
        reject(f"object {iso_id} is not under construction")

    xp_to_add = 0
    item_cfg = get_item_config(ctx.game_config, item_data[0])
    if item_cfg:
        xp_to_add = item_cfg.get("xp", 0)

    ctx.info[Resource.XP] += xp_to_add

    item_data[3] = 0
    del item_data[6]["tb"]

    logger.info("Finished building %s (speed up: %s), xp gained: %s", iso_id, is_speed_up, xp_to_add)
