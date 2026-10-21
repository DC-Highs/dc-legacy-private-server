"""Minigame rewards.

The client reports how many gems it won and the server cannot verify a minigame, so the
reward is bounded instead: a few gems, at most once per cooldown.
"""
import logging
import time

from flask import Blueprint, jsonify
from pydantic import BaseModel, ConfigDict, Field

from src import storage
from src.api import parse_body
from src.auth.context import current_user, login_required
from src.enums import Resource
from src.errors import ApiError, not_found

logger = logging.getLogger(__name__)

bp = Blueprint("minigames", __name__)

MAX_GEMS_PER_GAME = 3
COOLDOWN_SECONDS = 60


class RewardBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    gems: int = Field(ge=0, le=MAX_GEMS_PER_GAME)


@bp.post("/minigame/reward")
@login_required
def minigame_reward():
    body = parse_body(RewardBody)
    player_id = current_user().id

    if body.gems == 0:
        return jsonify({"status": "ok", "gems_earned": 0, "new_cash": None})

    now = int(time.time())
    with storage.player_lock(player_id):
        if now - storage.get_last_minigame_ts(player_id) < COOLDOWN_SECONDS:
            raise ApiError(429, "too_many_requests", "Wait a moment before playing again")

        player_data = storage.load_player(player_id)
        if player_data is None:
            raise not_found("Player not found")

        current_cash = player_data["playerInfo"].get(Resource.CASH, 0)
        new_cash = current_cash + body.gems
        player_data["playerInfo"][Resource.CASH] = new_cash

        storage.save_player(player_data, player_id)
        storage.set_last_minigame_ts(player_id, now)

    logger.info("Minigame: player %s earned %s gem(s) | %s -> %s", player_id, body.gems, current_cash, new_cash)
    return jsonify({"status": "ok", "gems_earned": body.gems, "new_cash": new_cash})
