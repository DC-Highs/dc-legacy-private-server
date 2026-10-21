"""Data the web client needs to start the Flash game."""
from flask import Blueprint, jsonify

from dragon_city import storage
from dragon_city.auth.context import current_user, login_required
from dragon_city.config import LEGACY_GAME_HOSTS, get_settings

bp = Blueprint("api_game", __name__, url_prefix="/api/game")

SERVICES_PATH = "/static/dragoncity/"


@bp.get("/bootstrap")
@login_required
def bootstrap():
    user = current_user()
    settings = get_settings()
    doc = storage.peek_player(user.id)

    return jsonify({
        "playerId": str(user.id),
        "playerName": doc["playerInfo"].get("name", "") if doc else "",
        "loader": "flash/DCLoader.swf",
        "servicesPath": SERVICES_PATH,
        # Variables the Flash client reads; the web client adds the services URL of this server.
        "flashVars": {
            "swftoload": "flash/" + settings.swf_version,
            "use_assets_opt": True,
            "fb_sig_user": str(user.id),
            "language": "en",
            "skiphash12341": "",
            "user_key": "12304531",
            "getText": "",
            "push_time": "1",
            "offer_type": "1",
            "fb_promo_uri": "",
            "spdebug": "0",
            "fb_sig_friends": "100000030",
        },
        "legacyHosts": list(LEGACY_GAME_HOSTS),
    })


@bp.get("/health")
def health():
    """Liveness probe for Docker: both databases must answer."""
    from sqlalchemy import text

    from dragon_city.db.mongo import get_db
    from dragon_city.db.postgres import get_engine

    with get_engine().connect() as connection:
        connection.execute(text("SELECT 1"))
    get_db().command("ping")
    return jsonify({"status": "ok"})
