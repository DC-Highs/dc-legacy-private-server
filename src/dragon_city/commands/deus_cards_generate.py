import logging
import random

from dragon_city.commands.base import CommandContext, command
from dragon_city.enums import Command, Resource

logger = logging.getLogger(__name__)

PRIZE_COUNT = 9
DEFAULT_SUPER_TRY_COST = 10
DEFAULT_TRY_COST = 3


@command(Command.DEUS_CARDS_GENERATE)
def handle(ctx: CommandContext) -> None:
    is_paid = int(ctx.args[0]) if len(ctx.args) > 0 else 0
    is_super = int(ctx.args[1]) if len(ctx.args) > 1 else 0

    globals_config = ctx.game_config.get("globals", {})

    if is_super == 1:
        cost = globals_config.get("DRAGON_CARDS_SUPER_TRY", {}).get("value", DEFAULT_SUPER_TRY_COST)
        ctx.info[Resource.CASH] = max(0, ctx.info[Resource.CASH] - cost)
    elif is_paid == 1:
        cost = globals_config.get("DRAGON_CARDS_TRY", {}).get("value", DEFAULT_TRY_COST)
        ctx.info[Resource.CASH] = max(0, ctx.info[Resource.CASH] - cost)

    prize_id = random.randint(0, PRIZE_COUNT - 1)

    if "deus_cards" not in ctx.private_state:
        ctx.private_state["deus_cards"] = {}
    ctx.private_state["deus_cards"]["pending_prize"] = prize_id

    ctx.result = prize_id
    logger.info("Card draw generated, prize id: %s", prize_id)
