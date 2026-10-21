import logging
import time

from dragon_city.commands.base import CommandContext, command
from dragon_city.enums import Command, Resource
from dragon_city.game.items import get_item_config
from dragon_city.game.map_items import clear_habitat_arrival

logger = logging.getLogger(__name__)


@command(Command.HATCH_EGG)
def handle(ctx: CommandContext) -> None:
    egg_uid = ctx.args[0]
    habitat_uid = ctx.args[2]
    dragon_name = ctx.args[3]

    clear_habitat_arrival(ctx.player_data, str(habitat_uid), ctx.server_ts)

    egg_data = None
    if "eggs" in ctx.map:
        for i, egg in enumerate(ctx.map["eggs"]):
            if str(egg.get("id")) == str(egg_uid):
                egg_data = ctx.map["eggs"].pop(i)
                break

    if not egg_data:
        logger.warning("No egg with uid %s found in the incubator", egg_uid)
        return

    dragon_type_id = egg_data.get("type")
    item_cfg = get_item_config(ctx.game_config, dragon_type_id)

    if not item_cfg:
        logger.warning("No config found for dragon %s in the game config", dragon_type_id)
        return

    hatch_xp = item_cfg.get("xp", 0)
    ctx.info[Resource.XP] += hatch_xp

    if "dragons" not in ctx.map:
        ctx.map["dragons"] = []

    ctx.map["dragons"].append({
        "id": egg_uid,
        "type": dragon_type_id,
        "xp": 0,
        "habitatId": habitat_uid,
        "name": dragon_name,
        "ts": int(time.time()),
        "work_id": [],
        "nbKill": 0,
        "attack": item_cfg.get("attacks", 0),
    })

    if "ownedDragons" not in ctx.map:
        ctx.map["ownedDragons"] = {}

    id_str = str(dragon_type_id)
    if id_str not in ctx.map["ownedDragons"]:
        ctx.map["ownedDragons"][id_str] = [1, 0, 0]

    logger.info("Hatched dragon %s (type %s) in habitat %s", dragon_name, dragon_type_id, habitat_uid)
    logger.info("XP gained: %s | total XP: %s", hatch_xp, ctx.info[Resource.XP])
    logger.info("Dragon %s (type %s) added to the dragon book", dragon_name, dragon_type_id)
