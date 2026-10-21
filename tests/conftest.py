"""Test fixtures: SQLite for accounts, mongomock for game state, no external services."""
import json
import re
import sys
from pathlib import Path

import mongomock
import pytest
from sqlalchemy.pool import StaticPool

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from dragon_city import storage  # noqa: E402
from dragon_city.app import create_app  # noqa: E402
from dragon_city.config import get_settings  # noqa: E402
from dragon_city.db.models import Base  # noqa: E402
from dragon_city.db.mongo import init_mongo  # noqa: E402
from dragon_city.db.postgres import init_engine  # noqa: E402
from dragon_city.extensions import limiter  # noqa: E402

PASSWORD = "correct horse battery"


@pytest.fixture()
def app():
    engine = init_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    init_mongo(mongomock.MongoClient(tz_aware=True), "test")
    get_settings.cache_clear()
    flask_app = create_app(run_startup=False)
    flask_app.config["TESTING"] = True
    limiter.reset()
    from dragon_city.game.pvp import seed_pvp_data

    seed_pvp_data()
    yield flask_app
    engine.dispose()


@pytest.fixture()
def client(app):
    return app.test_client()


def register(client, email="player@example.com", password=PASSWORD):
    return client.post("/api/auth/register", json={"email": email, "password": password, "confirmPassword": password})


@pytest.fixture()
def player(client):
    """A registered, logged-in player (the client keeps the session cookie)."""
    response = register(client)
    assert response.status_code == 201, response.get_data(as_text=True)
    return response.get_json()["user"]


def create_admin_client(app, email="admin@example.com"):
    from dragon_city.auth import service
    from dragon_city.db.postgres import session_scope

    with session_scope() as session:
        service.create_user(session, email, PASSWORD, is_admin=True)
    admin_client = app.test_client()
    response = admin_client.post("/api/auth/login", json={"email": email, "password": PASSWORD})
    assert response.status_code == 200
    return admin_client


@pytest.fixture()
def admin_client(app):
    return create_admin_client(app)


def packet(client, *commands):
    """Send commands through packet.php and return the decoded response list."""
    payload = "sig;" + json.dumps({"commands": [
        {"cmd": c[0], "args": list(c[1]) if len(c) > 1 else [], "number": i} for i, c in enumerate(commands, 1)
    ]})
    response = client.post("/static/dragoncity/srv/packet.php", data={"data": payload})
    assert response.status_code == 200, response.get_data(as_text=True)
    body = response.get_data(as_text=True).split(";", 1)[1]
    return json.loads(body)["response"]


def load_save(player_id):
    return storage.peek_player(int(player_id))


def edit_save(player_id, mutate):
    """Change a player's save directly in the database (to set up a scenario)."""
    with storage.player_lock(int(player_id)):
        data = storage.load_player(int(player_id))
        mutate(data)
        storage.save_player(data, int(player_id))
