"""Administration API: manage accounts and their game saves."""
import logging
from typing import Optional

from flask import Blueprint, jsonify, request
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import func, or_, select

from src import friends, storage
from src.api import parse_body
from src.auth import service
from src.auth.context import admin_required, current_user
from src.db.models import User
from src.db.postgres import session_scope
from src.errors import ApiError, forbidden, not_found, validation_error
from src.game.pvp import generate_pvp_opponents

logger = logging.getLogger(__name__)

bp = Blueprint("api_admin", __name__, url_prefix="/api/admin")

MAX_PAGE_SIZE = 100
MAX_RESOURCE = 2_000_000_000


class CreateUserBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: str = Field(max_length=254)
    password: str = Field(max_length=256)
    is_admin: bool = Field(default=False, alias="isAdmin")


class UpdateUserBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: Optional[str] = Field(default=None, max_length=254)
    password: Optional[str] = Field(default=None, max_length=256)
    is_admin: Optional[bool] = Field(default=None, alias="isAdmin")
    is_active: Optional[bool] = Field(default=None, alias="isActive")


class AddFriendBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    friend_id: int = Field(alias="friendId", ge=1, le=2 ** 53)


class ResourcesBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    gold: Optional[int] = Field(default=None, ge=0, le=MAX_RESOURCE)
    cash: Optional[int] = Field(default=None, ge=0, le=MAX_RESOURCE)
    food: Optional[int] = Field(default=None, ge=0, le=MAX_RESOURCE)


def _get_user(session, user_id: int) -> User:
    user = session.get(User, user_id)
    if user is None:
        raise not_found("User not found")
    return user


def _user_with_player(user: User):
    doc = storage.peek_player(user.id)
    return service.user_to_dict(user, storage.player_summary(doc) if doc else None)


@bp.get("/users")
@admin_required
def list_users():
    query = (request.args.get("query") or "").strip()[:100]
    try:
        page = max(1, int(request.args.get("page", 1)))
        page_size = min(MAX_PAGE_SIZE, max(1, int(request.args.get("pageSize", 20))))
    except ValueError:
        raise validation_error({"page": "page and pageSize must be integers"})

    statement = select(User)
    count = select(func.count()).select_from(User)
    if query:
        pattern = "%" + query.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%"
        condition = User.email.ilike(pattern, escape="\\")
        if query.isdigit():
            condition = or_(condition, User.id == int(query))
        statement = statement.where(condition)
        count = count.where(condition)

    with session_scope() as session:
        total = session.scalar(count) or 0
        users = session.scalars(
            statement.order_by(User.id.desc()).offset((page - 1) * page_size).limit(page_size)
        ).all()

    summaries = storage.players_summaries([u.id for u in users])
    return jsonify({
        "items": [service.user_to_dict(u, summaries.get(u.id)) for u in users],
        "total": total,
        "page": page,
        "pageSize": page_size,
    })


@bp.post("/users")
@admin_required
def create_user():
    body = parse_body(CreateUserBody)
    with session_scope() as session:
        user = service.create_user(session, body.email, body.password, is_admin=body.is_admin)
        payload = _user_with_player(user)
    logger.info("Admin %s created account %s", current_user().id, payload["id"])
    response = jsonify({"user": payload})
    response.status_code = 201
    return response


@bp.get("/users/<int:user_id>")
@admin_required
def get_user(user_id: int):
    with session_scope() as session:
        return jsonify({"user": _user_with_player(_get_user(session, user_id))})


@bp.patch("/users/<int:user_id>")
@admin_required
def update_user(user_id: int):
    body = parse_body(UpdateUserBody)
    me = current_user()
    with session_scope() as session:
        user = _get_user(session, user_id)

        if user.id == me.id and (body.is_active is False or body.is_admin is False):
            raise forbidden("You cannot disable or demote your own account")

        if body.email is not None:
            email = service.normalize_email(body.email)
            taken = session.scalar(select(User).where(User.email == email, User.id != user.id))
            if taken is not None:
                raise ApiError(409, "conflict", "This email is already registered", {"email": "Already registered"})
            user.email = email
        if body.password is not None:
            service.check_password(body.password, user.email)
            user.password_hash = service.hash_password(body.password)
            service.end_all_sessions(session, user.id)
        if body.is_admin is not None:
            user.is_admin = body.is_admin
        if body.is_active is not None:
            user.is_active = body.is_active
            if not body.is_active:
                service.end_all_sessions(session, user.id)

        payload = _user_with_player(user)
    logger.info("Admin %s updated account %s", me.id, user_id)
    return jsonify({"user": payload})


@bp.delete("/users/<int:user_id>")
@admin_required
def delete_user(user_id: int):
    me = current_user()
    if user_id == me.id:
        raise forbidden("You cannot delete your own account")
    with session_scope() as session:
        user = _get_user(session, user_id)
        session.delete(user)
    storage.delete_player(user_id)
    logger.info("Admin %s deleted account %s", me.id, user_id)
    return jsonify({"ok": True})


@bp.post("/users/<int:user_id>/reset-player")
@admin_required
def reset_player(user_id: int):
    with session_scope() as session:
        user = _get_user(session, user_id)
        with storage.player_lock(user.id):
            storage.create_player(user.id, storage.default_player_name(user.email), replace=True)
        payload = _user_with_player(user)
    logger.info("Admin %s reset the game save of account %s", current_user().id, user_id)
    return jsonify({"user": payload})


@bp.patch("/users/<int:user_id>/resources")
@admin_required
def set_resources(user_id: int):
    body = parse_body(ResourcesBody)
    changes = body.model_dump(exclude_none=True)
    if not changes:
        raise validation_error({"_": "Provide at least one of gold, cash, food"})

    with session_scope() as session:
        user = _get_user(session, user_id)
        with storage.player_lock(user.id):
            data = storage.load_player(user.id)
            if data is None:
                raise not_found("Game save not found")
            data["playerInfo"].update(changes)
            storage.save_player(data, user.id)
        payload = _user_with_player(user)
    logger.info("Admin %s set resources %s of account %s", current_user().id, changes, user_id)
    return jsonify({"user": payload})


@bp.post("/pvp/generate")
@admin_required
def generate_pvp():
    total = generate_pvp_opponents()
    return jsonify({"totalOpponents": total})


def _friend_entry(user: User) -> dict:
    doc = storage.peek_player(user.id)
    return {"id": user.id, "email": user.email, "playerName": doc["playerInfo"].get("name", "") if doc else ""}


@bp.get("/users/<int:user_id>/friends")
@admin_required
def list_friends(user_id: int):
    with session_scope() as session:
        _get_user(session, user_id)
        return jsonify({"items": [_friend_entry(u) for u in friends.friends_of(session, user_id)]})


@bp.post("/users/<int:user_id>/friends")
@admin_required
def add_friend(user_id: int):
    body = parse_body(AddFriendBody)
    with session_scope() as session:
        _get_user(session, user_id)
        friends.add_friends(session, user_id, body.friend_id)
        items = [_friend_entry(u) for u in friends.friends_of(session, user_id)]
    logger.info("Admin %s made %s and %s friends", current_user().id, user_id, body.friend_id)
    response = jsonify({"items": items})
    response.status_code = 201
    return response


@bp.delete("/users/<int:user_id>/friends/<int:friend_id>")
@admin_required
def remove_friend(user_id: int, friend_id: int):
    with session_scope() as session:
        _get_user(session, user_id)
        if not friends.remove_friends(session, user_id, friend_id):
            raise not_found("They are not friends")
        items = [_friend_entry(u) for u in friends.friends_of(session, user_id)]
    logger.info("Admin %s ended the friendship of %s and %s", current_user().id, user_id, friend_id)
    return jsonify({"items": items})
