import logging
import time

from dragon_city.commands.base import CommandContext, command
from dragon_city.enums import Command

logger = logging.getLogger(__name__)


@command(Command.START_TRAINING)
def handle(ctx: CommandContext) -> None:
    building_uid = str(ctx.args[0])
    dragon_uid = ctx.args[1]
    attack_id = ctx.args[2]
    attack_pos = ctx.args[3]

    if "work" not in ctx.map:
        ctx.map["work"] = {}

    ctx.map["work"][building_uid] = [dragon_uid, attack_id, int(time.time()), attack_pos]

    for dragon in ctx.map.get("dragons", []):
        if str(dragon.get("id")) == str(dragon_uid):
            dragon["work_id"] = int(building_uid)
            logger.info("Dragon %s (id %s) entered the training center", dragon.get("name", "Unknown"), dragon_uid)
            break

    logger.info("Building %s is training attack %s in slot %s", building_uid, attack_id, attack_pos)
