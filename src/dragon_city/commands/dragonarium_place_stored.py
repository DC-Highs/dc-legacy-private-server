import logging
import time

from dragon_city.commands.base import CommandContext, command
from dragon_city.commands.validation import reject
from dragon_city.enums import Command, GroupType
from dragon_city.game.dragonarium import has_free_slot, tab_for_attributes
from dragon_city.game.inventory import register_owned_dragon, take_stored_dragon

logger = logging.getLogger(__name__)


@command(Command.DRAGONARIUM_PLACE_STORED)
def handle(ctx: CommandContext) -> None:
    dragon_name = ctx.text_arg(0, "dragon name")
    dragon_type_id = ctx.int_arg(1, "dragon type", 1)
    claimed_level = ctx.int_arg(2, "dragon level", 0, 100)
    is_gift = ctx.flag_arg(3, "is gift")

    item_cfg = ctx.item_config(dragon_type_id)
    if item_cfg.get("group_type") != GroupType.DRAGON:
        reject(f"item {dragon_type_id} is not a dragon")

    tab = tab_for_attributes(item_cfg.get("attributes", []))
    if not has_free_slot(ctx.private_state, tab):
        reject(f"the dragonarium tab {tab.name} is full")

    dragon_lvl, list_name = take_stored_dragon(ctx.player_data, dragon_type_id, claimed_level, is_gift == 1)
    if dragon_lvl is None:
        reject(f"dragon type {dragon_type_id} (level {claimed_level}) is not in {list_name}")
    dragon_xp = 4 * dragon_lvl - 4

    dragon_uid = int(time.time() * 1000)
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
