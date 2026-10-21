import logging
import time

from dragon_city.commands.base import CommandContext, command
from dragon_city.commands.validation import reject
from dragon_city.enums import Command, GroupType, Resource
from dragon_city.game.items import get_item_config
from dragon_city.game.map_items import clear_habitat_arrival

logger = logging.getLogger(__name__)


@command(Command.HATCH_EGG)
def handle(ctx: CommandContext) -> None:
    egg_uid = ctx.uid_arg(0, "egg uid")
    habitat_iso = ctx.iso_arg(2, "habitat")
    habitat_uid = ctx.args[2]  # stored exactly as the client sent it
    dragon_name = ctx.text_arg(3, "dragon name")

    habitat = ctx.map_item(habitat_iso)
    habitat_cfg = get_item_config(ctx.game_config, habitat[0])
    if not habitat_cfg or habitat_cfg.get("group_type") != GroupType.HABITAT:
        reject(f"object {habitat_iso} is not a habitat")

    egg_data = ctx.find_egg(egg_uid)
    item_cfg = get_item_config(ctx.game_config, egg_data.get("type"))
    if not item_cfg:
        reject(f"no config found for dragon {egg_data.get('type')}")

    clear_habitat_arrival(ctx.player_data, habitat_iso, ctx.server_ts)
    ctx.map["eggs"].remove(egg_data)

    dragon_type_id = egg_data.get("type")
    hatch_xp = item_cfg.get("xp", 0)
    ctx.info[Resource.XP] += hatch_xp

    ctx.map["dragons"].append({
        "id": egg_data.get("id"),
        "type": dragon_type_id,
        "xp": 0,
        "habitatId": habitat_uid,
        "name": dragon_name,
        "ts": int(time.time()),
        "work_id": [],
        "nbKill": 0,
        "attack": item_cfg.get("attacks", 0),
    })

    id_str = str(dragon_type_id)
    if id_str not in ctx.map["ownedDragons"]:
        ctx.map["ownedDragons"][id_str] = [1, 0, 0]

    logger.info("Hatched dragon %s (type %s) in habitat %s", dragon_name, dragon_type_id, habitat_uid)
    logger.info("XP gained: %s | total XP: %s", hatch_xp, ctx.info[Resource.XP])
    logger.info("Dragon %s (type %s) added to the dragon book", dragon_name, dragon_type_id)
