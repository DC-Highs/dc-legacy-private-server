import logging
import random

from dragon_city.commands.base import CommandContext, command
from dragon_city.commands.validation import reject
from dragon_city.enums import Command
from dragon_city.game.black_market import roll_kompu_pool

logger = logging.getLogger(__name__)


@command(Command.KOMPU_BOXES_CLAIM_PRIZE)
def handle(ctx: CommandContext) -> None:
    private_state = ctx.private_state
    current_opened = private_state.get("kompuBoxesOpened", 0)
    kompu_dragons = private_state.get("kompuBoxesDragons", [])

    if not (current_opened > 0 and len(kompu_dragons) >= current_opened):
        reject(f"kompuBoxesOpened is {current_opened}, invalid list to claim from")

    prize_dragon_id = kompu_dragons[current_opened - 1]
    ctx.map["store"]["dragons"].append({"iid": prize_dragon_id, "lvl": 0})
    logger.info("Dragon %s stored in the warehouse", prize_dragon_id)

    private_state["kompuBoxesOpened"] = 0

    pool_dragons, unique_included = roll_kompu_pool(ctx.game_config)

    if unique_included:
        logger.info("The special dragon (%s) appeared in the new pool after claiming", pool_dragons[-1])

    private_state["kompuBoxesDragons"] = pool_dragons[:]

    shuffled_dragons = pool_dragons[:]
    random.shuffle(shuffled_dragons)
    private_state["kompuBoxesShuffledDragons"] = shuffled_dragons

    ctx.result = {
        "kompuBoxesDragons": private_state["kompuBoxesDragons"],
        "kompuBoxesShuffledDragons": private_state["kompuBoxesShuffledDragons"],
    }

    logger.info("Board reset")
