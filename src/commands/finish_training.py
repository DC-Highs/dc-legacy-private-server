import logging
import time

from src.commands.base import CommandContext, command
from src.commands.validation import reject
from src.enums import Command
from src.game.training import TRAINING_TOLERANCE_SECONDS, teach_attack, training_time

logger = logging.getLogger(__name__)


@command(Command.FINISH_TRAINING)
def handle(ctx: CommandContext) -> None:
    building_uid = ctx.iso_arg(0, "training building")

    work = ctx.map["work"]
    if building_uid not in work:
        reject(
            f"building {building_uid} was not registered in 'work' "
            "(it probably finished already or the client is out of sync)"
        )
    work_data = work[building_uid]

    dragon = ctx.find_dragon(work_data[0])
    attack_id = int(work_data[1])
    attack_pos = int(work_data[3])

    # speed_training moves the start back, so a plain finish only works once the time is over.
    elapsed = int(time.time()) - int(work_data[2])
    if elapsed + TRAINING_TOLERANCE_SECONDS < training_time(ctx.game_config, attack_id):
        reject(f"training in building {building_uid} is not finished yet")

    teach_attack(dragon, attack_id, attack_pos)
    del work[building_uid]
    logger.info("Training finished, work queue cleared in building %s", building_uid)
