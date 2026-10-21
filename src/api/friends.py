"""Friend requests between players (the friends become neighbours in the game)."""
import logging
from typing import Any, Dict, List

from flask import Blueprint, jsonify
from pydantic import BaseModel, ConfigDict, Field

from src import friends, storage
from src.api import parse_body
from src.auth.context import current_user, login_required
from src.db.models import Friendship, User
from src.db.postgres import session_scope
from src.errors import not_found
from src.extensions import limiter, player_key

logger = logging.getLogger(__name__)

bp = Blueprint("api_friends", __name__, url_prefix="/api/friends")


class RequestBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    player_id: int = Field(alias="playerId", ge=1, le=2 ** 53)


def _people(user_ids: List[int]) -> Dict[int, Dict[str, Any]]:
    """Public profile of players: id, in-game name and level. Never the email."""
    summaries = storage.players_summaries(user_ids)
    return {
        uid: {"id": uid, "playerName": summaries[uid]["name"] if uid in summaries else "",
              "level": summaries[uid]["level"] if uid in summaries else 1}
        for uid in user_ids
    }


def _overview(session, user_id: int) -> Dict[str, Any]:
    friend_users = friends.friends_of(session, user_id)
    incoming, outgoing = friends.pending_requests(session, user_id)

    ids = [u.id for u in friend_users] + [r.requester_id for r in incoming] + [friends.addressee_id(r) for r in outgoing]
    people = _people(ids)

    return {
        "playerId": user_id,
        "friends": [people[u.id] for u in friend_users],
        "incoming": [
            {"requestId": r.id, "createdAt": r.created_at.isoformat(), "from": people[r.requester_id]}
            for r in incoming
        ],
        "outgoing": [
            {"requestId": r.id, "createdAt": r.created_at.isoformat(), "to": people[friends.addressee_id(r)]}
            for r in outgoing
        ],
        "limits": {"maxFriends": friends.max_friends(), "maxPendingRequests": friends.max_pending_requests(),
                   "rewardGems": friends.FRIEND_REWARD_GEMS,
                   "rewardLimit": friends.FRIEND_REWARD_LIMIT},
    }


@bp.get("")
@login_required
def overview():
    with session_scope() as session:
        return jsonify(_overview(session, current_user().id))


@bp.get("/summary")
@login_required
def summary():
    """How many requests wait for an answer (the header badge polls this)."""
    with session_scope() as session:
        return jsonify({"incoming": friends.count_incoming(session, current_user().id)})


@bp.post("/requests")
@login_required
@limiter.limit("30 per hour;10 per minute", key_func=player_key)
def send_request():
    body = parse_body(RequestBody)
    me = current_user().id
    with session_scope() as session:
        row, accepted = friends.send_request(session, me, body.player_id)
        request_id = row.id
    gems = friends.award_both(me, body.player_id).get(me, 0) if accepted else 0
    logger.info("Player %s asked %s to be friends (accepted at once: %s)", me, body.player_id, accepted)
    response = jsonify({"requestId": request_id, "accepted": accepted, "gemsAwarded": gems})
    response.status_code = 201
    return response


@bp.post("/requests/<int:request_id>/accept")
@login_required
def accept(request_id: int):
    me = current_user().id
    with session_scope() as session:
        row = friends.accept_request(session, me, request_id)
        requester = row.requester_id
    gems = friends.award_both(me, requester).get(me, 0)
    logger.info("Player %s accepted the friend request of %s", me, requester)
    return jsonify({"ok": True, "gemsAwarded": gems})


@bp.post("/requests/<int:request_id>/decline")
@login_required
def decline(request_id: int):
    with session_scope() as session:
        friends.decline_request(session, current_user().id, request_id)
    return jsonify({"ok": True})


@bp.delete("/requests/<int:request_id>")
@login_required
def cancel(request_id: int):
    with session_scope() as session:
        friends.cancel_request(session, current_user().id, request_id)
    return jsonify({"ok": True})


@bp.delete("/<int:player_id>")
@login_required
def remove(player_id: int):
    with session_scope() as session:
        if not friends.remove_friends(session, current_user().id, player_id):
            raise not_found("They are not your friend")
    logger.info("Player %s removed %s from their friends", current_user().id, player_id)
    return jsonify({"ok": True})
