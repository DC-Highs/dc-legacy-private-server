import logging
import random
import time

from dragon_city.commands.base import CommandContext, command
from dragon_city.commands.validation import reject
from dragon_city.enums import Command
from dragon_city.names import DRAGON_NAMES

logger = logging.getLogger(__name__)


@command(Command.FINISH_BREEDING2)
def handle(ctx: CommandContext) -> None:
    breeding_iso_id = ctx.iso_arg(0, "breeding cave")
    new_egg_uid = ctx.new_uid(1, "egg uid")
    hatchery_iso_id = ctx.iso_arg(2, "hatchery")

    work_data = ctx.map["work"].get(breeding_iso_id)
    if not work_data:
        reject(f"no breeding data found for building {breeding_iso_id}")

    dragon_id = work_data[4]

    ctx.map["eggs"].append({
        "id": new_egg_uid,
        "type": dragon_id,
        "name": random.choice(DRAGON_NAMES),
        "xp": 0,
        "ts": int(time.time()),
    })

    del ctx.map["work"][breeding_iso_id]

    if breeding_iso_id in ctx.map["items"]:
        ctx.map["items"][breeding_iso_id][3] = 0

    logger.info("Finished breeding in %s", breeding_iso_id)
    logger.info("Created egg of dragon %s (uid %s), moved to hatchery %s", dragon_id, new_egg_uid, hatchery_iso_id)

    ctx.result = dragon_id
