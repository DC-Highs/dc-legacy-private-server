import logging
import random
import time

from src.commands.base import CommandContext, command
from src.commands.validation import reject
from src.enums import Command

logger = logging.getLogger(__name__)

PRIZE_COUNT = 9
DEFAULT_SUPER_TRY_COST = 10
DEFAULT_TRY_COST = 3
# A free draw is available once per day, or right away after winning the "retry" prize.
FREE_DRAW_COOLDOWN_SECONDS = 24 * 3600


@command(Command.DEUS_CARDS_GENERATE)
def handle(ctx: CommandContext) -> None:
    is_paid = ctx.flag_arg(0, "is paid") if len(ctx.args) > 0 else 0
    is_super = ctx.flag_arg(1, "is super") if len(ctx.args) > 1 else 0

    globals_config = ctx.game_config.get("globals", {})
    private_state = ctx.private_state

    if is_super == 1:
        ctx.pay(cash=globals_config.get("DRAGON_CARDS_SUPER_TRY", {}).get("value", DEFAULT_SUPER_TRY_COST))
    elif is_paid == 1:
        ctx.pay(cash=globals_config.get("DRAGON_CARDS_TRY", {}).get("value", DEFAULT_TRY_COST))
    else:
        has_retry = bool(private_state.get("deusFreeRetry"))
        last_claim = int(private_state.get("deusCardsLastTimestamp") or 0)
        if not has_retry and int(time.time()) - last_claim < FREE_DRAW_COOLDOWN_SECONDS:
            reject("the free card draw is not available yet")
        pending = (private_state.get("deus_cards") or {}).get("pending_prize") if isinstance(private_state.get("deus_cards"), dict) else None
        if pending is not None:
            reject("claim the pending card prize before drawing again")
        # Consume the free draw now, not at claim time, so it cannot be re-rolled for free.
        private_state["deusFreeRetry"] = False
        private_state["deusCardsLastTimestamp"] = int(time.time())

    prize_id = random.randint(0, PRIZE_COUNT - 1)

    if not isinstance(private_state.get("deus_cards"), dict):
        private_state["deus_cards"] = {}
    private_state["deus_cards"]["pending_prize"] = prize_id

    ctx.result = prize_id
    logger.info("Card draw generated, prize id: %s", prize_id)
