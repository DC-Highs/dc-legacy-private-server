import logging

from dragon_city.commands.base import CommandContext, command
from dragon_city.enums import Command, Resource

logger = logging.getLogger(__name__)

DEFAULT_SPEED_UP_PRICE = 2
DEFAULT_COOLDOWN_HOURS = 12


@command(Command.ADMIN_SPEED_TOURNAMENT)
def handle(ctx: CommandContext) -> None:
    globals_config = ctx.game_config.get("globals", {})

    speed_up_price = globals_config.get("TOURNAMENT_SPEED_UP_PRICE", {}).get("value", DEFAULT_SPEED_UP_PRICE)
    cooldown_hours = globals_config.get("TOURNAMENT_COOLDOWN", {}).get("value", DEFAULT_COOLDOWN_HOURS)
    cooldown_seconds = cooldown_hours * 3600

    ctx.pay(cash=speed_up_price)

    current_end_ts = ctx.private_state.get("beginTournamentTs", 0)
    new_ts = max(0, current_end_ts - cooldown_seconds)
    ctx.private_state["beginTournamentTs"] = new_ts

    logger.info("Tournament sped up, cost: %s gems", speed_up_price)
    logger.info("New beginTournamentTs: %s | remaining gems: %s", new_ts, ctx.info[Resource.CASH])
