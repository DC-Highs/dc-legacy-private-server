"""Game files served to the logged-in web client, plus the built single-page app."""
import logging
from pathlib import Path

from flask import Blueprint, abort, jsonify, send_from_directory

from dragon_city.auth.context import login_required
from dragon_city.config import PIXEL_GIF, get_settings

logger = logging.getLogger(__name__)

bp = Blueprint("pages", __name__)
spa_bp = Blueprint("spa", __name__)

DEFAULT_CROSSDOMAIN = (
    '<?xml version="1.0"?><cross-domain-policy><allow-access-from domain="*"/></cross-domain-policy>'
)
RESERVED_PREFIXES = ("api/", "static/", "flash/", "assets/", "deploy/", "stream")


@bp.route("/flash/<path:path>")
@login_required
def serve_flash(path):
    return send_from_directory(get_settings().flash_dir, path)


@bp.route("/assets/<path:path>")
@login_required
def serve_assets(path):
    return send_from_directory(get_settings().assets_dir, path)


@bp.route("/sp-translations.socialpointgames.com/crossdomain.xml")
@bp.route("/crossdomain.xml")
def serve_crossdomain():
    directory = get_settings().domain_map_dir / "api.omniata.com"
    if (directory / "crossdomain.xml").exists():
        return send_from_directory(directory, "crossdomain.xml")
    return DEFAULT_CROSSDOMAIN, 200, {"Content-Type": "application/xml"}


@bp.route("/deploy/dc/canvas/prod/<filename>")
@login_required
def serve_translations(filename):
    directory = (
        get_settings().domain_map_dir / "sp-translations.socialpointgames.com" / "deploy" / "dc" / "canvas" / "prod"
    )
    if (directory / filename).exists():
        return send_from_directory(directory, filename)
    return jsonify({"error": "Translation file not found"}), 404


@bp.route("/__utm.gif")
@bp.route("/ga.js")
def serve_ga_stub():
    return PIXEL_GIF, 200, {"Content-Type": "image/gif"}


@spa_bp.route("/", defaults={"path": ""})
@spa_bp.route("/<path:path>")
def serve_spa(path):
    """Serve the Vite build; unknown paths fall back to index.html for client-side routing."""
    if path.startswith(RESERVED_PREFIXES):
        abort(404)

    dist: Path = get_settings().frontend_dist
    if not (dist / "index.html").exists():
        return jsonify({"error": "The web client is not built (frontend/dist is missing)"}), 503

    candidate = (dist / path).resolve()
    if path and candidate.is_file() and dist.resolve() in candidate.parents:
        return send_from_directory(dist, path)
    if "." in path.rsplit("/", 1)[-1]:
        abort(404)  # a missing file, not a page of the web client
    return send_from_directory(dist, "index.html")
