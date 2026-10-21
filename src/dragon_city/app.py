"""Flask application factory."""
import logging

from flask import Flask
from flask_cors import CORS

from dragon_city.routes import register_blueprints

logger = logging.getLogger(__name__)


def create_app() -> Flask:
    app = Flask(__name__, static_folder=None)
    CORS(app)
    register_blueprints(app)
    return app
