"""Flask integration: loads the logged-in user and protects state-changing requests."""
from functools import wraps
from typing import Callable, Optional
from urllib.parse import urlsplit

from flask import Flask, Response, g, request

from src.auth import service
from src.config import get_settings
from src.db.models import User
from src.db.postgres import session_scope
from src.errors import forbidden, unauthorized

SESSION_COOKIE = "dc_session"
UNSAFE_METHODS = ("POST", "PUT", "PATCH", "DELETE")


def current_user() -> Optional[User]:
    return getattr(g, "user", None)


def _load_user() -> None:
    g.user = None
    g.session_token = request.cookies.get(SESSION_COOKIE)
    if g.session_token:
        with session_scope() as session:
            g.user = service.resolve_session(session, g.session_token)


def _origin_allowed(origin: str) -> bool:
    origin = origin.rstrip("/")
    if origin in get_settings().allowed_origins:
        return True
    return urlsplit(origin).netloc == request.host


def _check_origin() -> None:
    """Reject cross-site state-changing requests (CSRF) when the browser tells us the origin."""
    if request.method not in UNSAFE_METHODS:
        return
    origin = request.headers.get("Origin")
    if origin is None:
        referer = request.headers.get("Referer")
        if referer is None:
            return  # not a browser request, so no ambient cookie can be abused
        origin = "{0.scheme}://{0.netloc}".format(urlsplit(referer))
    if origin == "null" or not _origin_allowed(origin):
        raise forbidden("Cross-site request blocked")


def set_session_cookie(response: Response, token: str) -> None:
    settings = get_settings()
    response.set_cookie(
        SESSION_COOKIE,
        token,
        max_age=settings.session_days * 86400,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="Lax",
        path="/",
    )


def clear_session_cookie(response: Response) -> None:
    response.delete_cookie(SESSION_COOKIE, path="/", samesite="Lax", secure=get_settings().cookie_secure)


def login_required(view: Callable) -> Callable:
    @wraps(view)
    def wrapper(*args, **kwargs):
        if current_user() is None:
            raise unauthorized()
        return view(*args, **kwargs)

    return wrapper


def admin_required(view: Callable) -> Callable:
    @wraps(view)
    def wrapper(*args, **kwargs):
        user = current_user()
        if user is None:
            raise unauthorized()
        if not user.is_admin:
            raise forbidden("Administrator access required")
        return view(*args, **kwargs)

    return wrapper


def init_auth(app: Flask) -> None:
    @app.before_request
    def _before_request():
        _check_origin()
        _load_user()

    @app.after_request
    def _security_headers(response: Response) -> Response:
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "same-origin")
        if request.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store"
        return response
