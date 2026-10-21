import logging
import time

from src.commands.base import CommandContext, command
from src.enums import Command

logger = logging.getLogger(__name__)


def _find_item_config(all_items, type_id: str):
    if isinstance(all_items, dict):
        return all_items.get(type_id)
    return next((i for i in all_items if str(i.get("id")) == type_id), None)


@command(Command.UPGRADE)
def handle(ctx: CommandContext) -> None:
    unique_id = ctx.iso_arg(0)

    item_data = ctx.map_item(unique_id)
    current_type_id = str(item_data[0])

    all_items = ctx.game_config.get("items", {})
    current_item_conf = _find_item_config(all_items, current_type_id)

    if not current_item_conf or "upgrades_to" not in current_item_conf:
        return

    new_type_id = str(current_item_conf["upgrades_to"])
    new_item_conf = _find_item_config(all_items, new_type_id)

    if not new_item_conf:
        return

    item_data[0] = int(new_type_id)
    build_time = new_item_conf.get("build_time", 0)
    current_ts = int(time.time())

    while len(item_data) < 7:
        item_data.append(0)

    if not isinstance(item_data[6], dict):
        item_data[6] = {}

    if build_time > 0:
        item_data[6]["tb"] = current_ts + build_time
    else:
        item_data[6].pop("tb", None)
        item_data[3] = 0

    logger.info("Upgraded item %s to type %s, tb: %s", unique_id, new_type_id, item_data[6].get("tb"))
