import logging

from dragon_city.commands.base import CommandContext, command
from dragon_city.enums import Command
from dragon_city.game.inventory import register_owned_dragon, remove_stored_dragon
from dragon_city.game.items import get_item_config
from dragon_city.game.map_items import clear_habitat_arrival

logger = logging.getLogger(__name__)


@command(Command.PLACE_STORED_DRAGON)
def handle(ctx: CommandContext) -> None:
    dragon_uid = ctx.args[0]
    habitat_uid = str(ctx.args[1])
    dragon_name = ctx.args[2]
    dragon_type_id = int(ctx.args[3])
    dragon_lvl = int(ctx.args[4])
    is_gift = int(ctx.args[5])

    dragon_xp = 4 * dragon_lvl - 4

    item_cfg = get_item_config(ctx.game_config, dragon_type_id)
    if not item_cfg:
        logger.warning("Dragon %s does not exist in the game config", dragon_type_id)
        return

    removed, list_name = remove_stored_dragon(ctx.player_data, dragon_type_id, is_gift == 1)

    if removed:
        logger.info("Removed dragon type %s from %s", dragon_type_id, list_name)
    else:
        logger.warning("Dragon type %s not found in '%s', placing it anyway", dragon_type_id, list_name)

    current_ts = ctx.server_ts
    clear_habitat_arrival(ctx.player_data, habitat_uid, current_ts)

    ctx.map["dragons"].append({
        "id": dragon_uid,
        "type": dragon_type_id,
        "xp": dragon_xp,
        "habitatId": habitat_uid,
        "name": dragon_name,
        "ts": current_ts,
        "work_id": [],
        "nbKill": 0,
        "attack": item_cfg.get("attacks", []),
    })

    register_owned_dragon(ctx.player_data, dragon_type_id, dragon_xp)

    logger.info(
        "Placed dragon %s (type %s) in habitat %s with xp %s",
        dragon_name, dragon_type_id, habitat_uid, dragon_xp,
    )
