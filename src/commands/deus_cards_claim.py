import logging
import time

from src.commands.base import CommandContext, command
from src.commands.validation import reject
from src.enums import Command, Resource

logger = logging.getLogger(__name__)

RETRY_REWARD = "retry"


@command(Command.DEUS_CARDS_CLAIM)
def handle(ctx: CommandContext) -> None:
    current_time = int(time.time())
    deus_cards = ctx.private_state.get("deus_cards")
    prize_id = deus_cards.get("pending_prize") if isinstance(deus_cards, dict) else None

    # The prize comes from a draw the server generated and is claimed only once.
    if prize_id is None:
        reject("there is no pending card prize to claim")

    prize_cfg = next((p for p in ctx.game_config.get("dragon_card_prizes", []) if p.get("id") == prize_id), None)
    deus_cards["pending_prize"] = None

    if prize_cfg:
        reward = prize_cfg.get("reward", {})

        if isinstance(reward, dict):
            gold_reward = reward.get("g", 0)
            food_reward = reward.get("f", 0)
            cash_reward = reward.get("c", 0)

            ctx.info[Resource.GOLD] += gold_reward
            ctx.info[Resource.FOOD] += food_reward
            ctx.info[Resource.CASH] += cash_reward

            logger.info("Prize claimed: gold +%s | food +%s | gems +%s", gold_reward, food_reward, cash_reward)

        elif isinstance(reward, int):
            ctx.map["store"]["dragons"].append({"iid": reward, "lvl": 0})
            logger.info("Prize claimed: dragon %s", reward)

        elif reward == RETRY_REWARD:
            ctx.private_state["deusFreeRetry"] = True
            logger.info("Prize: retry (free extra draw)")
            return

    ctx.private_state["deusCardsLastTimestamp"] = current_time
