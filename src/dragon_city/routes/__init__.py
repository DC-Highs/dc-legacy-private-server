"""HTTP routes, grouped in blueprints."""
from flask import Flask

from dragon_city.routes import account, market, minigames, packet, pages, srv, tools


def register_blueprints(app: Flask) -> None:
    for module in (pages, srv, packet, account, minigames, market, tools):
        app.register_blueprint(module.bp)
