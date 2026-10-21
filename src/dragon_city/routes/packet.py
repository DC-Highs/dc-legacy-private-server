"""The ``packet.php`` endpoint: applies batched client commands to the player save."""
import json
import logging
import time

from flask import Blueprint, request

from dragon_city.commands.base import implemented_commands, load_commands
from dragon_city.commands.dispatcher import dispatch_commands
from dragon_city.enums import SseEvent
from dragon_city.security import sign_packet
from dragon_city.state import notify
from dragon_city.storage import load_game_config, load_player, save_player

logger = logging.getLogger(__name__)

bp = Blueprint("packet", __name__)


def _process_post(user_id):
    data_raw = request.form.get("data", "")
    json_str = data_raw.split(";", 1)[1] if ";" in data_raw else data_raw

    payload = json.loads(json_str)
    player_data = load_player(user_id)
    game_config = load_game_config(user_id)

    outcome = dispatch_commands(user_id, player_data, game_config, payload.get("commands", []))

    save_player(player_data, user_id)
    player_data["timestamp"] = int(time.time())

    if outcome.applied_any:
        logger.info("Game saved for player %s (pid %s)", player_data["playerInfo"]["name"], user_id)
    else:
        logger.info("No changes applied, none of the received commands is implemented: %s", outcome.ignored)

    notify(user_id, SseEvent.GAME_SAVED)
    return outcome.responses


@bp.route("/static/dragoncity/srv/packet.php", methods=["POST", "GET"])
def packet_handler():
    user_id = request.args.get("USERID") or request.form.get("id")
    logger.info("Packet received for user %s", user_id)

    response_results = []

    if request.method == "POST":
        try:
            response_results = _process_post(user_id)
        except Exception:
            logger.exception("Failed to process packet.php")

    response_data = {
        "result": True,
        "response": response_results,
        "ts": int(time.time()),
        "publishActions": 0,
    }
    return sign_packet(response_data)


def log_command_coverage() -> None:
    load_commands()
    logger.info("Packet protocol: %s commands implemented", len(implemented_commands()))
