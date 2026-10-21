import logging
import time

from dragon_city.commands.base import CommandContext, command
from dragon_city.enums import Command, Resource

logger = logging.getLogger(__name__)

RETRY_REWARD = "retry"


@command(Command.DEUS_CARDS_CLAIM)
def handle(ctx: CommandContext) -> None:
    current_time = int(time.time())
    prize_id = ctx.private_state.get("deus_cards", {}).get("pending_prize", 0)

    prize_cfg = None
    for prize in ctx.game_config.get("dragon_card_prizes", []):
        if prize.get("id") == prize_id:
            prize_cfg = prize
            break

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
            logger.info("Prize: retry (free extra draw)")

    if "deus_cards" in ctx.private_state:
        ctx.private_state["deus_cards"]["pending_prize"] = None

    ctx.private_state["deusCardsLastTimestamp"] = current_time
