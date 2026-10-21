import logging
import random

from src.commands.base import CommandContext, command
from src.enums import Command
from src.game.black_market import roll_kompu_pool

logger = logging.getLogger(__name__)

NEW_LIST_PRICE = 3


@command(Command.KOMPU_BOXES_NEW_LIST)
def handle(ctx: CommandContext) -> None:
    ctx.pay(cash=NEW_LIST_PRICE)

    pool_dragons, unique_included = roll_kompu_pool(ctx.game_config)

    if unique_included:
        logger.info("The unique dragon (%s) appeared in the pool", pool_dragons[-1])

    private_state = ctx.private_state
    private_state["kompuBoxesDragons"] = pool_dragons[:]

    shuffled_dragons = pool_dragons[:]
    random.shuffle(shuffled_dragons)
    private_state["kompuBoxesShuffledDragons"] = shuffled_dragons

    ctx.result = {
        "kompuBoxesDragons": private_state["kompuBoxesDragons"],
        "kompuBoxesShuffledDragons": private_state["kompuBoxesShuffledDragons"],
    }

    logger.info("New kompu dragon list generated")
