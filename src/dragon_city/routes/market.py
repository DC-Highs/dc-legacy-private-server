"""Achievement-points market endpoints (act on the logged-in player)."""
import logging
import time

from flask import Blueprint, jsonify
from pydantic import BaseModel, ConfigDict, Field

from dragon_city import storage
from dragon_city.api import parse_body
from dragon_city.auth.context import current_user, login_required
from dragon_city.enums import OfferType, Resource
from dragon_city.errors import ApiError, not_found
from dragon_city.game.market import ensure_private_state, grant_dragon_to_player, load_or_create_market, save_market

logger = logging.getLogger(__name__)

bp = Blueprint("market", __name__)

RESOURCE_OFFERS = {
    OfferType.GOLD: (Resource.GOLD, "+{amount} gold"),
    OfferType.FOOD: (Resource.FOOD, "+{amount} food"),
    OfferType.GEMS: (Resource.CASH, "+{amount} gems"),
}


class RedeemBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    offer_id: int = Field(alias="offer_id", ge=1, le=1000)


@bp.get("/market_data")
@login_required
def market_data_endpoint():
    player_id = current_user().id
    with storage.player_lock(player_id):
        player_data = storage.load_player(player_id)
        if player_data is None:
            raise not_found("Player not found")

        player_data = ensure_private_state(player_data)
        storage.save_player(player_data, player_id)
        market_data = load_or_create_market(player_id)

    remaining = max(0, market_data.get("next_refresh_at", 0) - int(time.time()))
    return jsonify({
        "player_name": player_data["playerInfo"].get("name", ""),
        "achievement_points": player_data["privateState"]["achievement_points"],
        "next_refresh_seconds": remaining,
        "offers": market_data["offers"],
    })


@bp.post("/market/redeem")
@login_required
def market_redeem():
    body = parse_body(RedeemBody)
    player_id = current_user().id

    with storage.player_lock(player_id):
        player_data = storage.load_player(player_id)
        if player_data is None:
            raise not_found("Player not found")
        player_data = ensure_private_state(player_data)

        market_data = load_or_create_market(player_id)
        offer = next((o for o in market_data["offers"] if o["id"] == body.offer_id), None)

        if not offer:
            raise not_found("Offer not found")
        if offer.get("sold"):
            raise ApiError(400, "already_redeemed", "This offer was already redeemed")

        points = player_data["privateState"]["achievement_points"]
        if points < offer["cost"]:
            raise ApiError(400, "not_enough_points", "Not enough points")

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

        save_market(player_id, market_data)
        storage.save_player(player_data, player_id)

    logger.info("Market: player %s redeemed offer %s (%s) for %s points",
                player_id, body.offer_id, offer_type, offer["cost"])

    return jsonify({
        "status": "ok",
        "message": message,
        "new_points": player_data["privateState"]["achievement_points"],
    })
