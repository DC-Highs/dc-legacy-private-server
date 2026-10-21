import logging
import time

from dragon_city.commands.base import CommandContext, command
from dragon_city.enums import Command
from dragon_city.game.dragonarium import tab_for_attributes
from dragon_city.game.inventory import register_owned_dragon, remove_stored_dragon
from dragon_city.game.items import get_item_config

logger = logging.getLogger(__name__)


@command(Command.DRAGONARIUM_PLACE_STORED)
def handle(ctx: CommandContext) -> None:
    dragon_name = ctx.args[0]
    dragon_type_id = int(ctx.args[1])
    dragon_lvl = int(ctx.args[2])
    is_gift = int(ctx.args[3])

    dragon_uid = int(time.time() * 1000)
    dragon_xp = 4 * dragon_lvl - 4

    item_cfg = get_item_config(ctx.game_config, dragon_type_id)
    if not item_cfg:
        logger.error("Dragon %s does not exist in the game config, request discarded", dragon_type_id)
        return

    removed, list_name = remove_stored_dragon(ctx.player_data, dragon_type_id, is_gift == 1)

    if removed:
        logger.info("Consumed dragon type %s (%s) from %s", dragon_type_id, dragon_name, list_name)
    else:
        logger.warning("Dragon type %s not found in '%s', forcing its creation", dragon_type_id, list_name)

    tab = tab_for_attributes(item_cfg.get("attributes", []))

    ctx.private_state["dragonarium"][tab].append({
        "id": dragon_uid,
        "type": dragon_type_id,
        "xp": dragon_xp,
        "habitatId": 0,
        "name": dragon_name,
        "ts": ctx.server_ts,
        "work_id": [],
        "nbKill": 0,
        "attack": item_cfg.get("attacks", []),
    })

    register_owned_dragon(ctx.player_data, dragon_type_id, dragon_xp)

    logger.info(
        "Stored '%s' (type %s) in the dragonarium (tab %s), assigned uid %s",
        dragon_name, dragon_type_id, tab.name, dragon_uid,
    )
