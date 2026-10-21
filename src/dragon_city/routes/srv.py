"""Signed JSON endpoints under /static/dragoncity/srv, tracking stubs and the SSE stream.

Every endpoint that touches game state acts on the logged-in account. The ``USERID``
the Flash client sends is ignored: trusting it would let anyone play as anyone else.
"""
import logging
import queue

from flask import Blueprint, current_app, jsonify, request

from dragon_city import storage
from dragon_city.auth.context import current_user, login_required
from dragon_city.config import SSE_KEEPALIVE_SECONDS
from dragon_city.enums import SrvEndpoint, SseEvent
from dragon_city.errors import ApiError, not_found, validation_error
from dragon_city.game.black_market import check_and_update_black_market
from dragon_city.game.pvp import pvp_page
from dragon_city.security import sign_packet
from dragon_city.state import get_channel

logger = logging.getLogger(__name__)

bp = Blueprint("srv", __name__)

GAME_CONFIG_FILES = (SrvEndpoint.GAME_CONFIG_JSON, SrvEndpoint.GAME_CONFIG_PHP)
PVP_ISLE_FILES = (SrvEndpoint.PVP_ISLE_JSON, SrvEndpoint.PVP_ISLE_PHP)
PLAYER_INFO_FILES = (SrvEndpoint.PLAYER_INFO_JSON, SrvEndpoint.PLAYER_INFO_PHP)
MAX_PVP_LEVEL = 1000


def _no_cache_response(body: str):
    response = current_app.response_class(response=body, status=200, mimetype="text/plain")
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    return response


def _visited_player_id(own_id: int):
    """The id of the neighbour being visited, or ``None`` when the player views their own island."""
    raw = request.form.get("user") or request.args.get("user")
    if raw in (None, "", "0"):
        return None
    try:
        target = int(raw)
    except ValueError:
        raise validation_error({"user": "user must be an integer"})
    return None if target == own_id else target


def _pvp_response(level_arg: str):
    try:
        level = int(level_arg)
    except ValueError:
        raise validation_error({"level": "level must be an integer"})
    level = min(max(level, 1), MAX_PVP_LEVEL)
    page = pvp_page(level)
    logger.info("PvP league %s -> %s opponents", level, len(page))
    return _no_cache_response(sign_packet(page))


def _own_player_info(player_id: int):
    with storage.player_lock(player_id):
        player_data = storage.load_player(player_id)
        if player_data is None:
            raise not_found("Game save not found")

        if not player_data["playerInfo"].get("pid"):
            player_data["playerInfo"]["pid"] = str(player_id)

        game_config = storage.config_for_player(player_id)
        player_data, game_config = check_and_update_black_market(player_data, player_id, game_config)
        storage.save_player(player_data, player_id)
    return player_data


@bp.route("/static/dragoncity/srv/<filename>", methods=["GET", "POST"])
@login_required
def srv_handler(filename):
    player_id = current_user().id
    target_id = _visited_player_id(player_id)

    logger.info("SRV request %s | player: %s | visiting: %s", filename, player_id, target_id)

    if filename in GAME_CONFIG_FILES:
        return _no_cache_response(sign_packet(storage.config_for_player(player_id)))

    if filename in PVP_ISLE_FILES or filename == SrvEndpoint.PVP_ISLE_INFO_PHP:
        return _pvp_response(request.args.get("level", "1"))

    if filename in PLAYER_INFO_FILES:
        if target_id is None:
            player_data = _own_player_info(player_id)
        else:
            player_data = storage.peek_player(target_id)
            if player_data is None:
                raise not_found("Neighbour not found")
            if not player_data["playerInfo"].get("pid"):
                player_data["playerInfo"]["pid"] = str(target_id)
        return sign_packet(player_data), 200, {"Content-Type": "text/plain; charset=utf-8"}

    return jsonify({"result": "200"})


@bp.route("/static/dragoncity/srv/sync_error_track.php", methods=["POST", "GET"])
def sync_error_handler():
    return "", 200


@bp.route("/static/dragoncity/srv/track_game_status.php", methods=["GET", "POST"])
def track_status_handler():
    return "", 200


@bp.route("/static/dragoncity/deity_world/track/open", methods=["POST"])
@bp.route("/static/dragoncity/deity_world/track/watch-tutorial", methods=["POST"])
def deity_world_track():
    return jsonify({"result": True}), 200


@bp.route("/stream")
@login_required
def stream():
    player_id = current_user().id
    channel = get_channel(player_id)

    def event_stream():
        while True:
            try:
                message = channel.get(timeout=SSE_KEEPALIVE_SECONDS)
                yield f"data: {message}\n\n"
            except queue.Empty:
                yield f"data: {SseEvent.PING.value}\n\n"
            except Exception:
                logger.exception("Error in the SSE channel of player %s", player_id)
                break

    logger.info("SSE channel opened for player %s", player_id)
    response = current_app.response_class(event_stream(), mimetype="text/event-stream")
    response.headers["Cache-Control"] = "no-cache"
    response.headers["X-Accel-Buffering"] = "no"
    return response
