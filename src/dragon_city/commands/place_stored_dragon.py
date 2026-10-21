import logging

from dragon_city.commands.base import CommandContext, command
from dragon_city.commands.validation import reject
from dragon_city.enums import Command, GroupType
from dragon_city.game.inventory import register_owned_dragon, take_stored_dragon
from dragon_city.game.items import get_item_config
from dragon_city.game.map_items import clear_habitat_arrival

logger = logging.getLogger(__name__)


@command(Command.PLACE_STORED_DRAGON)
def handle(ctx: CommandContext) -> None:
    dragon_uid = ctx.new_uid(0, "dragon uid")
    habitat_uid = ctx.iso_arg(1, "habitat")
    dragon_name = ctx.text_arg(2, "dragon name")
    dragon_type_id = ctx.int_arg(3, "dragon type", 1)
    claimed_level = ctx.int_arg(4, "dragon level", 0, 100)
    is_gift = ctx.flag_arg(5, "is gift")

    item_cfg = ctx.item_config(dragon_type_id)
    if item_cfg.get("group_type") != GroupType.DRAGON:
        reject(f"item {dragon_type_id} is not a dragon")

    habitat = ctx.map_item(habitat_uid)
    habitat_cfg = get_item_config(ctx.game_config, habitat[0])
    if not habitat_cfg or habitat_cfg.get("group_type") != GroupType.HABITAT:
        reject(f"object {habitat_uid} is not a habitat")

    dragon_lvl, list_name = take_stored_dragon(ctx.player_data, dragon_type_id, claimed_level, is_gift == 1)
    if dragon_lvl is None:
        reject(f"dragon type {dragon_type_id} (level {claimed_level}) is not in {list_name}")
    dragon_xp = 4 * dragon_lvl - 4

    logger.info("Removed dragon type %s from %s", dragon_type_id, list_name)

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
