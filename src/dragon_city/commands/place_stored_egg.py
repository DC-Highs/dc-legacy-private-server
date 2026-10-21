import logging
import random
import time

from dragon_city.commands.base import CommandContext, command
from dragon_city.enums import Command
from dragon_city.game.items import get_item_config
from dragon_city.names import DRAGON_NAMES

logger = logging.getLogger(__name__)


@command(Command.PLACE_STORED_EGG)
def handle(ctx: CommandContext) -> None:
    egg_uid = ctx.args[0]
    dragon_id = ctx.args[1]
    is_gift = int(ctx.args[2])

    item_cfg = get_item_config(ctx.game_config, dragon_id)
    if not item_cfg:
        logger.warning("Dragon %s does not exist in the game config", dragon_id)
        return

    removed = False
    list_name = ""

    if is_gift == 1:
        # Kept as in the original: 'giftsi' looks like a typo for 'gifts', so this
        # branch never finds a gift egg.
        if "privateState" in ctx.player_data and "giftsi" in ctx.private_state:
            gifts_list = ctx.private_state["gifts"]
            list_name = "gifts"

            for i, gift in enumerate(gifts_list):
                if gift.get("iid") == dragon_id or gift.get("type") == dragon_id:
                    gifts_list.pop(i)
                    removed = True
                    break
    else:
        if "store" in ctx.player_data.get("map", {}):
            if "dragons" in ctx.map["store"]:
                store_dragons = ctx.map["store"]["dragons"]
                for i, d in enumerate(store_dragons):
                    if d.get("iid") == dragon_id:
                        store_dragons.pop(i)
                        removed = True
                        list_name = "store -> dragons"
                        break

            if not removed and "items" in ctx.map["store"]:
                store_items = ctx.map["store"]["items"]
                str_dragon_id = str(dragon_id)

                if str_dragon_id in store_items:
                    if store_items[str_dragon_id] > 1:
                        store_items[str_dragon_id] -= 1
                    else:
                        del store_items[str_dragon_id]
                    removed = True
                    list_name = "store -> items"

    if not removed:
        logger.warning("Egg %s not found in the warehouse, aborting incubation to avoid duplicates", dragon_id)
        return

    logger.info("Removed egg of %s from %s", item_cfg.get("name", dragon_id), list_name)

    ctx.map["eggs"].append({
        "id": egg_uid,
        "type": dragon_id,
        "name": random.choice(DRAGON_NAMES),
        "xp": 0,
        "hatched": False,
        "ts": int(time.time()),
    })
    logger.info("Egg %s (%s) placed in the hatchery", egg_uid, item_cfg.get("name", dragon_id))
