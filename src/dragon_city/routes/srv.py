"""Signed JSON endpoints under /static/dragoncity/srv, tracking stubs and the SSE stream."""
import logging
import queue

from flask import Blueprint, current_app, jsonify, request

from dragon_city.config import PVP_PAGE_SIZE, SSE_KEEPALIVE_SECONDS
from dragon_city.enums import SrvEndpoint, SseEvent
from dragon_city.game.black_market import check_and_update_black_market
from dragon_city.security import sign_packet
from dragon_city.state import get_channel
from dragon_city.storage import load_game_config, load_player, load_pvp_isle, save_player

logger = logging.getLogger(__name__)

bp = Blueprint("srv", __name__)

GAME_CONFIG_FILES = (SrvEndpoint.GAME_CONFIG_JSON, SrvEndpoint.GAME_CONFIG_PHP)
PVP_ISLE_FILES = (SrvEndpoint.PVP_ISLE_JSON, SrvEndpoint.PVP_ISLE_PHP)
PLAYER_INFO_FILES = (SrvEndpoint.PLAYER_INFO_JSON, SrvEndpoint.PLAYER_INFO_PHP)


def _no_cache_response(body: str):
    response = current_app.response_class(response=body, status=200, mimetype="text/plain")
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    return response


def _pvp_page(user_id, level: int):
    start = (level - 1) * PVP_PAGE_SIZE
    page = load_pvp_isle(user_id)[start:start + PVP_PAGE_SIZE]
    logger.info("PvP league %s -> opponents %s to %s (%s found)", level, start, start + PVP_PAGE_SIZE - 1, len(page))
    return _no_cache_response(sign_packet(page))


@bp.route("/static/dragoncity/srv/<filename>", methods=["GET", "POST"])
def srv_handler(filename):
    user_id = request.args.get("USERID") or request.form.get("USERID")

    target_id = request.form.get("user") or request.args.get("user")
    is_visiting = bool(target_id and target_id not in ("0", "", user_id))
    if is_visiting:
        user_id = target_id

    logger.info("SRV request %s | user: %s", filename, user_id)

    if filename in GAME_CONFIG_FILES:
        return _no_cache_response(sign_packet(load_game_config(user_id)))

    if filename in PVP_ISLE_FILES or filename == SrvEndpoint.PVP_ISLE_INFO_PHP:
        return _pvp_page(user_id, int(request.args.get("level", 1)))

    if filename in PLAYER_INFO_FILES:
        player_data = load_player(user_id)

        if "playerInfo" in player_data:
            if not player_data["playerInfo"].get("pid"):
                player_data["playerInfo"]["pid"] = user_id

            if not is_visiting:
                game_config = load_game_config(user_id)
                player_data, game_config = check_and_update_black_market(player_data, user_id, game_config)
                save_player(player_data, user_id)
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
def stream():
    user_id = request.args.get("USERID")

    if not user_id:
        return "USERID is required", 400

    channel = get_channel(user_id)

    def event_stream():
        while True:
            try:
                message = channel.get(timeout=SSE_KEEPALIVE_SECONDS)
                yield f"data: {message}\n\n"
            except queue.Empty:
                yield f"data: {SseEvent.PING.value}\n\n"
            except Exception:
                logger.exception("Error in the SSE channel of player %s", user_id)
                break

    logger.info("SSE channel opened for player %s", user_id)
    return current_app.response_class(event_stream(), mimetype="text/event-stream")
