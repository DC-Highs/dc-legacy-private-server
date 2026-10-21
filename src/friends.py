"""Friendships between accounts. In the game they are the player's neighbours.

A friendship starts as a request (``pending``) from one account to another; accepting it makes
it ``accepted``, and only accepted friendships count as neighbours. A declined request is kept
(``declined``) for a while so the same person cannot be asked again and again.
"""
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src import storage
from src.db.models import Friendship, User
from src.errors import ApiError, conflict, not_found, validation_error

logger = logging.getLogger(__name__)

PENDING = "pending"
ACCEPTED = "accepted"
DECLINED = "declined"

MAX_FRIENDS = 170          # the game talks about "170 friends"
MAX_OUTGOING_REQUESTS = 50
DECLINE_COOLDOWN = timedelta(days=7)

# "Add a friend and get 5 gems": paid to both players, for their first FRIEND_REWARD_LIMIT friends.
FRIEND_REWARD_GEMS = 5
FRIEND_REWARD_LIMIT = 5


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _aware(value: datetime) -> datetime:
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


def _pair(a: int, b: int) -> Tuple[int, int]:
    return (a, b) if a < b else (b, a)


def addressee_id(friendship: Friendship) -> int:
    """The account that has to answer the request."""
    return friendship.low_id if friendship.requester_id == friendship.high_id else friendship.high_id


def other_id(friendship: Friendship, user_id: int) -> int:
    return friendship.high_id if friendship.low_id == user_id else friendship.low_id


def _get_row(session: Session, a: int, b: int) -> Optional[Friendship]:
    low, high = _pair(a, b)
    return session.scalar(select(Friendship).where(Friendship.low_id == low, Friendship.high_id == high))


def _involving(user_id: int):
    return or_(Friendship.low_id == user_id, Friendship.high_id == user_id)


# --- friends -----------------------------------------------------------------


def friend_ids(session: Session, user_id: int) -> List[int]:
    """Ids of the accepted friends of ``user_id``, oldest friendship first."""
    rows = session.execute(
        select(Friendship.low_id, Friendship.high_id)
        .where(Friendship.status == ACCEPTED, _involving(user_id))
        .order_by(Friendship.id)
    ).all()
    return [high if low == user_id else low for low, high in rows]


def count_friends(session: Session, user_id: int) -> int:
    return session.scalar(
        select(func.count()).select_from(Friendship).where(Friendship.status == ACCEPTED, _involving(user_id))
    ) or 0


def are_friends(session: Session, a: int, b: int) -> bool:
    if a == b:
        return False
    row = _get_row(session, a, b)
    return row is not None and row.status == ACCEPTED


def friends_of(session: Session, user_id: int) -> List[User]:
    ids = friend_ids(session, user_id)
    if not ids:
        return []
    users = {u.id: u for u in session.scalars(select(User).where(User.id.in_(ids)))}
    return [users[i] for i in ids if i in users]


def remove_friends(session: Session, a: int, b: int) -> bool:
    """End a friendship (or drop a pending request) between two accounts."""
    row = _get_row(session, a, b)
    if row is None or row.status != ACCEPTED:
        return False
    session.delete(row)
    return True


# --- requests ----------------------------------------------------------------


def _accept(session: Session, friendship: Friendship) -> None:
    for user_id in (friendship.low_id, friendship.high_id):
        if count_friends(session, user_id) >= MAX_FRIENDS:
            raise conflict("A friend list is full")
    friendship.status = ACCEPTED
    friendship.responded_at = _now()


def send_request(session: Session, requester_id: int, target_id: int) -> Tuple[Friendship, bool]:
    """Ask ``target_id`` to be friends. Returns the row and whether it ended up accepted.

    If the target had already asked the requester, the two requests meet and it is accepted.
    """
    if requester_id == target_id:
        raise validation_error({"playerId": "You cannot add yourself"})
    target = session.get(User, target_id)
    if target is None or not target.is_active:
        raise not_found("Player not found")

    row = _get_row(session, requester_id, target_id)
    if row is not None:
        if row.status == ACCEPTED:
            raise conflict("You are already friends")
        if row.status == PENDING:
            if row.requester_id == target_id:
                _accept(session, row)
                return row, True
            raise conflict("You already sent a request to this player")
        # declined: the same person cannot ask again for a while
        if row.requester_id == requester_id and row.responded_at is not None \
                and _now() - _aware(row.responded_at) < DECLINE_COOLDOWN:
            raise ApiError(429, "too_many_requests", "This player declined your request recently. Try again later.")

    outgoing = session.scalar(
        select(func.count()).select_from(Friendship).where(
            Friendship.status == PENDING, Friendship.requester_id == requester_id)
    ) or 0
    if outgoing >= MAX_OUTGOING_REQUESTS:
        raise conflict("You have too many pending requests")
    if count_friends(session, requester_id) >= MAX_FRIENDS:
        raise conflict("Your friend list is full")

    if row is None:
        low, high = _pair(requester_id, target_id)
        row = Friendship(low_id=low, high_id=high, requester_id=requester_id, status=PENDING)
        session.add(row)
    else:
        row.requester_id = requester_id
        row.status = PENDING
        row.created_at = _now()
        row.responded_at = None
    try:
        session.flush()
    except IntegrityError:
        session.rollback()
        raise conflict("You already sent a request to this player")
    return row, False


def _request_for_addressee(session: Session, user_id: int, request_id: int) -> Friendship:
    row = session.get(Friendship, request_id)
    if row is None or row.status != PENDING or addressee_id(row) != user_id:
        raise not_found("Request not found")
    return row


def accept_request(session: Session, user_id: int, request_id: int) -> Friendship:
    row = _request_for_addressee(session, user_id, request_id)
    _accept(session, row)
    return row


def decline_request(session: Session, user_id: int, request_id: int) -> None:
    row = _request_for_addressee(session, user_id, request_id)
    row.status = DECLINED
    row.responded_at = _now()


def cancel_request(session: Session, user_id: int, request_id: int) -> None:
    row = session.get(Friendship, request_id)
    if row is None or row.status != PENDING or row.requester_id != user_id:
        raise not_found("Request not found")
    session.delete(row)


def pending_requests(session: Session, user_id: int) -> Tuple[List[Friendship], List[Friendship]]:
    """(incoming, outgoing) pending requests of ``user_id``, newest first."""
    rows = session.scalars(
        select(Friendship).where(Friendship.status == PENDING, _involving(user_id)).order_by(Friendship.id.desc())
    ).all()
    incoming = [r for r in rows if r.requester_id != user_id]
    outgoing = [r for r in rows if r.requester_id == user_id]
    return incoming, outgoing


def count_incoming(session: Session, user_id: int) -> int:
    return session.scalar(
        select(func.count()).select_from(Friendship).where(
            Friendship.status == PENDING, _involving(user_id), Friendship.requester_id != user_id)
    ) or 0


def add_friends(session: Session, a: int, b: int) -> Friendship:
    """Make two existing, different accounts friends right away (used by administrators)."""
    if a == b:
        raise validation_error({"friendId": "An account cannot be its own friend"})
    if session.get(User, a) is None or session.get(User, b) is None:
        raise not_found("User not found")

    row = _get_row(session, a, b)
    if row is not None and row.status == ACCEPTED:
        raise conflict("They are already friends")
    if row is None:
        low, high = _pair(a, b)
        row = Friendship(low_id=low, high_id=high, requester_id=a, status=PENDING)
        session.add(row)
    _accept(session, row)
    try:
        session.flush()
    except IntegrityError:
        session.rollback()
        raise conflict("They are already friends")
    return row


# --- the game's view -----------------------------------------------------------


def neighbors_payload(session: Session, user_id: int) -> List[Dict[str, Any]]:
    """The ``neighbors`` list of ``get_player_info``: what the Flash client shows as friends."""
    ids = friend_ids(session, user_id)
    summaries = storage.players_summaries(ids)
    payload = []
    for friend_id in ids:
        summary = summaries.get(friend_id)
        if summary is None:
            continue
        payload.append({
            "pid": str(friend_id),
            "name": summary["name"],
            "xp": summary["xp"],
            "level": summary["level"],
            "world_id": 0,
        })
    return payload


def friends_flashvar(session: Session, user_id: int) -> str:
    """Value of the ``fb_sig_friends`` flash variable: the friend ids, comma separated."""
    return ",".join(str(i) for i in friend_ids(session, user_id))


def require_friendship(session: Session, user_id: int, other: Optional[int]) -> None:
    if other is None or not are_friends(session, user_id, other):
        raise not_found("Neighbour not found")


# --- the "5 gems" reward -----------------------------------------------------------


def award_friend_gems(player_id: int, friend_id: int) -> int:
    """Pay the new-friend gems to ``player_id``; returns how many were paid (0 if none).

    Only the first ``FRIEND_REWARD_LIMIT`` friends pay, and a friend pays once even if the
    friendship is ended and made again.
    """
    with storage.player_lock(player_id):
        data = storage.load_player(player_id)
        if data is None:
            return 0
        rewarded = data["privateState"].get("friendGemRewards")
        if not isinstance(rewarded, list):
            rewarded = data["privateState"]["friendGemRewards"] = []
        if friend_id in rewarded or len(rewarded) >= FRIEND_REWARD_LIMIT:
            return 0
        rewarded.append(friend_id)
        data["playerInfo"]["cash"] += FRIEND_REWARD_GEMS
        storage.save_player(data, player_id)
    logger.info("Player %s received %s gems for the friendship with %s", player_id, FRIEND_REWARD_GEMS, friend_id)
    return FRIEND_REWARD_GEMS


def award_both(a: int, b: int) -> Dict[int, int]:
    """Pay the reward to both sides of a new friendship; returns the gems each one received."""
    return {a: award_friend_gems(a, b), b: award_friend_gems(b, a)}
