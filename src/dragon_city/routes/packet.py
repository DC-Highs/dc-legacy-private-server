"""The ``packet.php`` endpoint: applies batched client commands to the logged-in player's save."""
import json
import logging
import time

from flask import Blueprint, request

from dragon_city import storage
from dragon_city.auth.context import current_user, login_required
from dragon_city.commands.base import implemented_commands, load_commands
from dragon_city.commands.dispatcher import dispatch_commands
from dragon_city.enums import SseEvent
from dragon_city.errors import ApiError, validation_error
from dragon_city.extensions import limiter, player_key
from dragon_city.security import sign_packet
from dragon_city.state import notify

logger = logging.getLogger(__name__)

bp = Blueprint("packet", __name__)

MAX_PACKET_BYTES = 256 * 1024


def _reject_constant(name: str):
    raise ValueError(f"invalid JSON constant {name}")


def _read_payload() -> dict:
    data_raw = request.form.get("data", "")
    if len(data_raw) > MAX_PACKET_BYTES:
        raise ApiError(413, "payload_too_large", "Packet too large")
    # The client sends "<signature>;<json>"; the signature uses a key that ships in the SWF,
    # so it proves nothing and is ignored.
    json_str = data_raw.split(";", 1)[1] if ";" in data_raw else data_raw
    try:
        payload = json.loads(json_str, parse_constant=_reject_constant)
    except ValueError:
        raise validation_error({"data": "The packet is not valid JSON"})
    if not isinstance(payload, dict):
        raise validation_error({"data": "The packet must be a JSON object"})
    return payload


def _process_post(player_id: int):
    payload = _read_payload()

    with storage.player_lock(player_id):
        player_data = storage.load_player(player_id)
        if player_data is None:
            raise ApiError(404, "not_found", "Game save not found")
        game_config = storage.config_for_player(player_id)

        outcome = dispatch_commands(player_id, player_data, game_config, payload.get("commands", []))

        storage.save_player(player_data, player_id)

    if outcome.applied_any:
        logger.info("Game saved for player %s (%s)", player_id, player_data["playerInfo"].get("name"))
    else:
        logger.info("No changes applied, none of the received commands is implemented: %s", outcome.ignored)

    notify(player_id, SseEvent.GAME_SAVED)
    return outcome.responses


@bp.route("/static/dragoncity/srv/packet.php", methods=["POST", "GET"])
@login_required
@limiter.limit("600 per minute", key_func=player_key)
def packet_handler():
    player_id = current_user().id
    logger.info("Packet received for player %s", player_id)

    response_results = _process_post(player_id) if request.method == "POST" else []

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
