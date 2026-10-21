"""Register, login, logout and the current user."""
import logging

from flask import Blueprint, g, jsonify, request
from pydantic import BaseModel, ConfigDict, Field

from src import storage
from src.api import parse_body
from src.auth import service
from src.auth.context import (
    clear_session_cookie,
    current_user,
    login_required,
    set_session_cookie,
)
from src.db.postgres import session_scope
from src.extensions import limiter

logger = logging.getLogger(__name__)

bp = Blueprint("api_auth", __name__, url_prefix="/api/auth")


class RegisterBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: str = Field(max_length=254)
    password: str = Field(max_length=256)
    confirm_password: str = Field(alias="confirmPassword", max_length=256)


class LoginBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: str = Field(max_length=254)
    password: str = Field(max_length=256)


def _me_payload(user):
    payload = service.user_to_dict(user)
    doc = storage.peek_player(user.id)
    payload["playerName"] = doc["playerInfo"].get("name", "") if doc else ""
    return payload


@bp.post("/register")
@limiter.limit("10 per hour;3 per minute")
def register():
    body = parse_body(RegisterBody)
    with session_scope() as session:
        user = service.register_user(session, body.email, body.password, body.confirm_password)
        token = service.start_session(session, user, request.remote_addr, request.user_agent.string)
        response = jsonify({"user": _me_payload(user)})
    response.status_code = 201
    set_session_cookie(response, token)
    return response


@bp.post("/login")
@limiter.limit("20 per hour;5 per minute")
def login():
    body = parse_body(LoginBody)
    with session_scope() as session:
        user = service.authenticate(session, body.email, body.password)
        service.ensure_player(user)
        token = service.start_session(session, user, request.remote_addr, request.user_agent.string)
        response = jsonify({"user": _me_payload(user)})
    set_session_cookie(response, token)
    logger.info("Account %s logged in", user.id)
    return response


@bp.post("/logout")
def logout():
    if getattr(g, "session_token", None):
        with session_scope() as session:
            service.end_session(session, g.session_token)
    response = jsonify({"ok": True})
    clear_session_cookie(response)
    return response


@bp.get("/me")
@login_required
def me():
    return jsonify({"user": _me_payload(current_user())})
