"""Developer tools exposed to templates/tools.html."""
import logging

from flask import Blueprint, jsonify

from dragon_city.game.pvp import generate_pvp_opponents

logger = logging.getLogger(__name__)

bp = Blueprint("tools", __name__)


@bp.route("/generate_pvp", methods=["POST"])
def generate_pvp():
    try:
        total = generate_pvp_opponents()
        return jsonify({"status": "ok", "total_opponents": total})

    except Exception as e:
        logger.exception("Error in /generate_pvp")
        return jsonify({"status": "error", "error": str(e)}), 500
