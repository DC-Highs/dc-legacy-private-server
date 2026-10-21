import logging
import math
import time

from dragon_city.commands.base import CommandContext, command
from dragon_city.enums import Command, Resource
from dragon_city.game.training import teach_attack

logger = logging.getLogger(__name__)


@command(Command.SPEED_TRAINING)
def handle(ctx: CommandContext) -> None:
    building_uid = str(ctx.args[0])

    work = ctx.map.get("work", {})
    if building_uid not in work:
        logger.warning("Building %s is not training (not found in 'work')", building_uid)
        return

    work_data = work[building_uid]

    start_ts = int(work_data[2])
    current_ts = int(time.time())

    dragon_uid = str(work_data[0])
    attack_id = int(work_data[1])
    attack_pos = int(work_data[3])

    attacks_db = ctx.game_config.get("attacks", {})
    training_time = 0

    if attack_id in attacks_db:
        training_time = attacks_db[attack_id].get("training_time", 0)

    time_left = max(0, training_time - (current_ts - start_ts))
    speed_up_cost = max(1, math.ceil(time_left / 3600.0))

    if ctx.info[Resource.CASH] >= speed_up_cost:
        ctx.info[Resource.CASH] -= speed_up_cost
        work[building_uid][2] = current_ts - training_time - 10

        logger.info("Training sped up, cost: %s gems", speed_up_cost)
        logger.info("Remaining gems: %s", ctx.info[Resource.CASH])
    else:
        logger.warning("Not enough gems to speed up the training")

    if teach_attack(ctx.player_data, dragon_uid, attack_id, attack_pos):
        del work[building_uid]
        logger.info("Training finished, work queue cleared in building %s", building_uid)
    else:
        logger.warning("Dragon %s not found on the map to teach it the attack", dragon_uid)
