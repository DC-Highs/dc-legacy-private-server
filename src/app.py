"""Flask application factory."""
import logging
from typing import Optional

from flask import Flask, jsonify, request
from werkzeug.exceptions import HTTPException
from werkzeug.middleware.proxy_fix import ProxyFix

from src.auth import service as auth_service
from src.auth.context import init_auth
from src.config import Settings, get_settings
from src.db.mongo import ensure_indexes
from src.db.postgres import session_scope
from src.errors import ApiError
from src.extensions import limiter
from src.game.pvp import seed_pvp_data
from src.routes import register_blueprints

logger = logging.getLogger(__name__)

MAX_REQUEST_BYTES = 1024 * 1024


def _register_error_handlers(app: Flask) -> None:
    @app.errorhandler(ApiError)
    def _api_error(exc: ApiError):
        return jsonify(exc.to_dict()), exc.status

    @app.errorhandler(HTTPException)
    def _http_error(exc: HTTPException):
        return jsonify({"error": {"code": exc.name.lower().replace(" ", "_"), "message": exc.description}}), exc.code

    @app.errorhandler(Exception)
    def _unexpected(exc: Exception):
        logger.exception("Unhandled error on %s %s", request.method, request.path)
        return jsonify({"error": {"code": "internal_error", "message": "Internal server error"}}), 500


def startup_tasks(settings: Optional[Settings] = None) -> None:
    """One-time work done when the server starts (indexes, seed data, bootstrap admin)."""
    settings = settings or get_settings()
    ensure_indexes()
    seed_pvp_data()
    with session_scope() as session:
        if settings.admin_email and settings.admin_password:
            auth_service.ensure_admin(session, settings.admin_email, settings.admin_password)
        auth_service.purge_expired_sessions(session)


def create_app(run_startup: bool = True) -> Flask:
    settings = get_settings()
    app = Flask(__name__, static_folder=None)
    app.config["MAX_CONTENT_LENGTH"] = MAX_REQUEST_BYTES
    app.json.sort_keys = False

    if settings.trust_proxy:
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

    init_auth(app)
    limiter.init_app(app)
    _register_error_handlers(app)
    register_blueprints(app)

    if run_startup:
        startup_tasks(settings)
    return app
