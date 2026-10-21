"""HTML pages and static files of the game."""
import logging

from flask import Blueprint, jsonify, request, send_from_directory

from dragon_city.config import (
    ASSETS_DIR,
    DOMAIN_MAP_DIR,
    FLASH_DIR,
    PIXEL_GIF,
    TEMPLATES_DIR,
)
from dragon_city.storage import load_player, save_player

logger = logging.getLogger(__name__)

bp = Blueprint("pages", __name__)

DEFAULT_CROSSDOMAIN = (
    '<?xml version="1.0"?><cross-domain-policy><allow-access-from domain="*"/></cross-domain-policy>'
)


@bp.route("/")
def serve_login():
    return send_from_directory(TEMPLATES_DIR, "login.html")


@bp.route("/index.html")
def serve_game():
    user_id = request.args.get("fb_sig_user")
    player_name = request.args.get("player_name")

    if user_id and player_name:
        player_data = load_player(user_id)

        if "playerInfo" in player_data:
            current_name = player_data["playerInfo"].get("name", "")

            if not current_name:
                player_data["playerInfo"]["name"] = player_name
                player_data["playerInfo"]["pid"] = user_id

                save_player(player_data, user_id)
                logger.info("New profile created from the URL -> pid: %s | name: %s", user_id, player_name)

    return send_from_directory(TEMPLATES_DIR, "index.html")


@bp.route("/flash/<path:path>")
def serve_flash(path):
    return send_from_directory(FLASH_DIR, path)


@bp.route("/assets/<path:path>")
def serve_assets(path):
    return send_from_directory(ASSETS_DIR, path)


@bp.route("/ajax/libs/swfobject/2.2/swfobject.js")
def serve_swfobject():
    directory = DOMAIN_MAP_DIR / "ajax.googleapis.com" / "ajax" / "libs" / "swfobject" / "2.2"
    if (directory / "swfobject.js").exists():
        return send_from_directory(directory, "swfobject.js")
    return "Not found", 404


@bp.route("/sp-translations.socialpointgames.com/crossdomain.xml")
@bp.route("/crossdomain.xml")
def serve_crossdomain():
    directory = DOMAIN_MAP_DIR / "api.omniata.com"
    if (directory / "crossdomain.xml").exists():
        return send_from_directory(directory, "crossdomain.xml")
    return DEFAULT_CROSSDOMAIN, 200, {"Content-Type": "application/xml"}


@bp.route("/deploy/dc/canvas/prod/<filename>")
def serve_translations(filename):
    directory = DOMAIN_MAP_DIR / "sp-translations.socialpointgames.com" / "deploy" / "dc" / "canvas" / "prod"
    if (directory / filename).exists():
        return send_from_directory(directory, filename)
    return jsonify({"error": "Translation file not found"}), 404


@bp.route("/__utm.gif")
@bp.route("/ga.js")
def serve_ga_stub():
    return PIXEL_GIF, 200, {"Content-Type": "image/gif"}


@bp.route("/minigames.html")
def serve_minigames():
    return send_from_directory(TEMPLATES_DIR, "minigames.html")


@bp.route("/market.html")
def serve_market():
    return send_from_directory(TEMPLATES_DIR, "market.html")


@bp.route("/tools.html")
def serve_tools():
    return send_from_directory(TEMPLATES_DIR, "tools.html")
