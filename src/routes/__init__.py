"""HTTP routes, grouped in blueprints."""
from flask import Flask

from src.api import admin, auth, game
from src.routes import market, minigames, packet, pages, srv


def register_blueprints(app: Flask) -> None:
    for module in (auth, admin, game, srv, packet, market, minigames, pages):
        app.register_blueprint(module.bp)
    # Registered last: the catch-all that serves the web client.
    app.register_blueprint(pages.spa_bp)
