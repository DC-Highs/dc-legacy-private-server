import logging
import random
import time

from dragon_city.commands.base import CommandContext, command
from dragon_city.commands.validation import reject
from dragon_city.enums import Command, GroupType
from dragon_city.names import DRAGON_NAMES

logger = logging.getLogger(__name__)


@command(Command.PLACE_STORED_EGG)
def handle(ctx: CommandContext) -> None:
    egg_uid = ctx.new_uid(0, "egg uid")
    dragon_id = ctx.int_arg(1, "dragon id", 1)
    is_gift = ctx.flag_arg(2, "is gift")

    item_cfg = ctx.item_config(dragon_id)
    if item_cfg.get("group_type") != GroupType.DRAGON:
        reject(f"item {dragon_id} is not a dragon")

    removed = False
    list_name = ""

    if is_gift == 1:
        # Kept as in the original: 'giftsi' looks like a typo for 'gifts', so this
        # branch never finds a gift egg.
        if "giftsi" in ctx.private_state:
            gifts_list = ctx.private_state["gifts"]
            list_name = "gifts"

            for i, gift in enumerate(gifts_list):
                if gift.get("iid") == dragon_id or gift.get("type") == dragon_id:
                    gifts_list.pop(i)
                    removed = True
                    break
    else:
        store = ctx.map["store"]
        for i, d in enumerate(store["dragons"]):
            if d.get("iid") == dragon_id:
                store["dragons"].pop(i)
                removed = True
                list_name = "store -> dragons"
                break

        if not removed:
            str_dragon_id = str(dragon_id)
            if str_dragon_id in store["items"]:
                if store["items"][str_dragon_id] > 1:
                    store["items"][str_dragon_id] -= 1
                else:
                    del store["items"][str_dragon_id]
                removed = True
                list_name = "store -> items"

    if not removed:
        reject(f"egg {dragon_id} not found in the warehouse")

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
