import json
import logging

from dragon_city.commands.base import CommandContext, command
from dragon_city.enums import Command
from dragon_city.storage import load_player, save_player

logger = logging.getLogger(__name__)


@command(Command.ASSIST_NEIGHBOR)
def handle(ctx: CommandContext) -> None:
    target_player_id = str(ctx.args[0])
    clicks = json.loads(ctx.args[1])

    victim_data = load_player(target_player_id)

    victim_data.setdefault("map", {})
    if not isinstance(victim_data["map"].get("receivedAssists"), dict):
        victim_data["map"]["receivedAssists"] = {}

    key = "u" + str(ctx.user_id)
    victim_data["map"]["receivedAssists"].setdefault(key, [])
    victim_data["map"]["receivedAssists"][key].extend(clicks)

    save_player(victim_data, target_player_id)

    logger.info("Helped neighbor %s", victim_data["playerInfo"]["name"])
