"""Achievement-points market endpoints."""
import logging
import time

from flask import Blueprint, jsonify, request

from dragon_city.enums import OfferType, Resource
from dragon_city.game.market import (
    ensure_private_state,
    grant_dragon_to_player,
    load_or_create_market,
    save_market,
)
from dragon_city.storage import load_player, save_player

logger = logging.getLogger(__name__)

bp = Blueprint("market", __name__)

RESOURCE_OFFERS = {
    OfferType.GOLD: (Resource.GOLD, "+{amount} gold"),
    OfferType.FOOD: (Resource.FOOD, "+{amount} food"),
    OfferType.GEMS: (Resource.CASH, "+{amount} gems"),
}


@bp.route("/market_data", methods=["GET"])
def market_data_endpoint():
    try:
        user_id = request.args.get("fb_sig_user")
        player_name = request.args.get("player_name", "DragonMaster")

        if not user_id:
            return jsonify({"error": "fb_sig_user is required"}), 400

        player_data = load_player(user_id)
        if "playerInfo" not in player_data:
            return jsonify({"error": "Player not found"}), 404

        player_data = ensure_private_state(player_data)
        save_player(player_data, user_id)

        market_data = load_or_create_market(user_id)
        remaining = max(0, market_data.get("next_refresh_at", 0) - int(time.time()))

        return jsonify({
            "player_name": player_data["playerInfo"].get("name", player_name),
            "achievement_points": player_data["privateState"]["achievement_points"],
            "next_refresh_seconds": remaining,
            "offers": market_data["offers"],
        })

    except Exception as e:
        logger.exception("Error in /market_data")
        return jsonify({"error": str(e)}), 500


@bp.route("/market/redeem", methods=["POST"])
def market_redeem():
    try:
        data = request.get_json(force=True)
        user_id = data.get("fb_sig_user")
        offer_id = data.get("offer_id")

        if not user_id or offer_id is None:
            return jsonify({"error": "fb_sig_user and offer_id are required"}), 400

        player_data = load_player(user_id)
        if "playerInfo" not in player_data:
            return jsonify({"error": "Player not found"}), 404

        player_data = ensure_private_state(player_data)

        market_data = load_or_create_market(user_id)
        offer = next((o for o in market_data["offers"] if o["id"] == offer_id), None)

        if not offer:
            return jsonify({"error": "Offer not found"}), 404
        if offer.get("sold"):
            return jsonify({"error": "This offer was already redeemed"}), 400

        points = player_data["privateState"]["achievement_points"]
        if points < offer["cost"]:
            return jsonify({"error": "Not enough points"}), 400

        player_data["privateState"]["achievement_points"] = points - offer["cost"]

        message = ""
        offer_type = offer["type"]
        if offer_type in RESOURCE_OFFERS:
            resource, template = RESOURCE_OFFERS[offer_type]
            player_data["playerInfo"][resource] += offer["amount"]
            message = template.format(amount=offer["amount"])
        elif offer_type == OfferType.DRAGON:
            grant_dragon_to_player(player_data, offer)
            message = f"New dragon: {offer['name']}!"

        offer["sold"] = True

        save_market(user_id, market_data)
        save_player(player_data, user_id)

        logger.info("Market: player %s redeemed offer %s (%s) for %s points", user_id, offer_id, offer_type, offer["cost"])

        return jsonify({
            "status": "ok",
            "message": message,
            "new_points": player_data["privateState"]["achievement_points"],
        })

    except Exception as e:
        logger.exception("Error in /market/redeem")
        return jsonify({"error": str(e)}), 500
