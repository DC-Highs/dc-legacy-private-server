import logging

from dragon_city.commands.base import CommandContext, command
from dragon_city.enums import Command, Resource
from dragon_city.game.items import get_item_config

logger = logging.getLogger(__name__)


@command(Command.FINISH_BUILDING)
def handle(ctx: CommandContext) -> None:
    iso_id = str(ctx.args[0])
    is_speed_up = ctx.args[1]

    if iso_id not in ctx.map["items"]:
        logger.warning("Iso id %s does not exist on the map", iso_id)
        return

    item_data = ctx.map["items"][iso_id]

    xp_to_add = 0
    item_cfg = get_item_config(ctx.game_config, item_data[0])
    if item_cfg:
        xp_to_add = item_cfg.get("xp", 0)

    ctx.info[Resource.XP] += xp_to_add

    item_data[3] = 0

    if len(item_data) > 6 and isinstance(item_data[6], dict):
        if "tb" in item_data[6]:
            del item_data[6]["tb"]
            logger.info("Removed 'tb' from iso id %s", iso_id)

    logger.info("Finished building %s (speed up: %s), xp gained: %s", iso_id, is_speed_up, xp_to_add)
