import logging
import math
import time

from src.commands.base import CommandContext, command
from src.commands.validation import reject
from src.enums import Command, Resource
from src.game.training import teach_attack, training_time

logger = logging.getLogger(__name__)


@command(Command.SPEED_TRAINING)
def handle(ctx: CommandContext) -> None:
    building_uid = ctx.iso_arg(0, "training building")

    work = ctx.map["work"]
    if building_uid not in work:
        reject(f"building {building_uid} is not training")
    work_data = work[building_uid]

    dragon = ctx.find_dragon(work_data[0])
    attack_id = int(work_data[1])
    attack_pos = int(work_data[3])
    start_ts = int(work_data[2])
    current_ts = int(time.time())

    total_time = training_time(ctx.game_config, attack_id)
    time_left = max(0, total_time - (current_ts - start_ts))
    speed_up_cost = max(1, math.ceil(time_left / 3600.0))

    ctx.pay(cash=speed_up_cost)

    logger.info("Training sped up, cost: %s gems", speed_up_cost)
    logger.info("Remaining gems: %s", ctx.info[Resource.CASH])

    teach_attack(dragon, attack_id, attack_pos)
    del work[building_uid]
    logger.info("Training finished, work queue cleared in building %s", building_uid)
