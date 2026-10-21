"""Minigame rewards."""
import logging

from flask import Blueprint, jsonify, request

from dragon_city.enums import Resource
from dragon_city.storage import load_player, save_player

logger = logging.getLogger(__name__)

bp = Blueprint("minigames", __name__)

MAX_GEMS_PER_GAME = 3


@bp.route("/minigame/reward", methods=["POST"])
def minigame_reward():
    try:
        data = request.get_json(force=True)

        user_id = data.get("user_id")
        gems = int(data.get("gems", 0))

        if not user_id:
            return jsonify({"status": "error", "msg": "user_id is required"}), 400
        if gems < 0 or gems > MAX_GEMS_PER_GAME:
            return jsonify({"status": "error", "msg": "Gem amount out of range"}), 400

        if gems == 0:
            return jsonify({"status": "ok", "gems_earned": 0, "new_cash": None})

        player_data = load_player(user_id)
        if "playerInfo" not in player_data:
            return jsonify({"status": "error", "msg": "Player not found"}), 404

        current_cash = player_data["playerInfo"].get(Resource.CASH, 0)
        new_cash = current_cash + gems
        player_data["playerInfo"][Resource.CASH] = new_cash

        save_player(player_data, user_id)

        logger.info("Minigame: player %s earned %s gem(s) | %s -> %s", user_id, gems, current_cash, new_cash)

        return jsonify({"status": "ok", "gems_earned": gems, "new_cash": new_cash})

    except Exception as e:
        logger.exception("Error in /minigame/reward")
        return jsonify({"status": "error", "msg": str(e)}), 500
