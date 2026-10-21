import logging

from dragon_city.commands.base import CommandContext, command
from dragon_city.enums import Command
from dragon_city.game.training import teach_attack

logger = logging.getLogger(__name__)


@command(Command.FINISH_TRAINING)
def handle(ctx: CommandContext) -> None:
    building_uid = str(ctx.args[0])

    work = ctx.map.get("work", {})
    if building_uid not in work:
        logger.warning(
            "Building %s was not registered in 'work' (it probably finished already or the client is out of sync)",
            building_uid,
        )
        return

    work_data = work[building_uid]

    dragon_uid = str(work_data[0])
    attack_id = int(work_data[1])
    attack_pos = int(work_data[3])

    if teach_attack(ctx.player_data, dragon_uid, attack_id, attack_pos):
        del work[building_uid]
        logger.info("Training finished, work queue cleared in building %s", building_uid)
    else:
        logger.warning("Dragon %s not found on the map to teach it the attack", dragon_uid)
