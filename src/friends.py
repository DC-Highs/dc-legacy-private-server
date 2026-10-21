"""Friendships between accounts. In the game they are the player's neighbours."""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src import storage
from src.db.models import Friendship, User
from src.errors import ApiError, conflict, not_found, validation_error

ACCEPTED = "accepted"


def _pair(a: int, b: int):
    return (a, b) if a < b else (b, a)


def friend_ids(session: Session, user_id: int) -> List[int]:
    """Ids of the accepted friends of ``user_id``, oldest friendship first."""
    rows = session.execute(
        select(Friendship.low_id, Friendship.high_id)
        .where(Friendship.status == ACCEPTED, or_(Friendship.low_id == user_id, Friendship.high_id == user_id))
        .order_by(Friendship.id)
    ).all()
    return [high if low == user_id else low for low, high in rows]


def are_friends(session: Session, a: int, b: int) -> bool:
    if a == b:
        return False
    low, high = _pair(a, b)
    return session.scalar(
        select(Friendship.id).where(Friendship.low_id == low, Friendship.high_id == high, Friendship.status == ACCEPTED)
    ) is not None


def add_friends(session: Session, a: int, b: int) -> Friendship:
    """Make two existing, different accounts friends right away (used by administrators)."""
    if a == b:
        raise validation_error({"friendId": "An account cannot be its own friend"})
    if session.get(User, a) is None or session.get(User, b) is None:
        raise not_found("User not found")

    low, high = _pair(a, b)
    friendship = Friendship(
        low_id=low, high_id=high, requester_id=a, status=ACCEPTED, responded_at=datetime.now(timezone.utc)
    )
    session.add(friendship)
    try:
        session.flush()
    except IntegrityError:
        session.rollback()
        raise conflict("They are already friends")
    return friendship


def remove_friends(session: Session, a: int, b: int) -> bool:
    low, high = _pair(a, b)
    friendship = session.scalar(select(Friendship).where(Friendship.low_id == low, Friendship.high_id == high))
    if friendship is None:
        return False
    session.delete(friendship)
    return True


def friends_of(session: Session, user_id: int) -> List[User]:
    ids = friend_ids(session, user_id)
    if not ids:
        return []
    users = {u.id: u for u in session.scalars(select(User).where(User.id.in_(ids)))}
    return [users[i] for i in ids if i in users]


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


def require_friendship(session: Session, user_id: int, other_id: Optional[int]) -> None:
    if other_id is None or not are_friends(session, user_id, other_id):
        raise not_found("Neighbour not found")
