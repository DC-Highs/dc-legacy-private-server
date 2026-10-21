import json

from conftest import PASSWORD, load_save
from src import storage
from src.config import DEUS_PLAYER_ID
from src.db.models import User
from src.db.postgres import session_scope
from src.system_accounts import DEUS_EMAIL, ensure_deus


def make_deus():
    with session_scope() as session:
        ensure_deus(session)


def visit(client, player_id):
    response = client.get(f"/static/dragoncity/srv/get_player_info.json?user={player_id}")
    body = json.loads(response.get_data(as_text=True).split(";", 1)[1]) if response.status_code == 200 else None
    return response, body


def test_deus_has_an_account_and_a_save(app):
    make_deus()
    make_deus()                                                   # running it again changes nothing
    with session_scope() as session:
        deus = session.get(User, DEUS_PLAYER_ID)
        assert deus.email == DEUS_EMAIL and deus.is_active is False and deus.is_admin is False
    assert load_save(DEUS_PLAYER_ID)["playerInfo"]["name"] == "Deus"
    assert storage.player_exists(DEUS_PLAYER_ID)


def test_everybody_can_visit_deus(app, client, player):
    make_deus()
    response, deus = visit(client, DEUS_PLAYER_ID)
    assert response.status_code == 200
    assert deus["playerInfo"]["name"] == "Deus" and deus["playerInfo"]["pid"] == str(DEUS_PLAYER_ID)


def test_visiting_deus_is_read_only(app, client, player):
    make_deus()
    before = load_save(DEUS_PLAYER_ID)["playerInfo"]
    visit(client, DEUS_PLAYER_ID)
    assert load_save(DEUS_PLAYER_ID)["playerInfo"] == before


def test_strangers_are_still_not_visitable(app, client, player):
    make_deus()
    other = app.test_client()
    other_id = other.post("/api/auth/register", json={"email": "o@example.com", "password": PASSWORD,
                                                      "confirmPassword": PASSWORD}).get_json()["user"]["id"]
    assert visit(client, other_id)[0].status_code == 404


def test_nobody_can_log_in_as_deus_or_befriend_him(app, client, player):
    make_deus()
    stranger = app.test_client()
    assert stranger.post("/api/auth/login", json={"email": DEUS_EMAIL, "password": "anything-at-all"}).status_code in (401, 403)
    assert client.post("/api/friends/requests", json={"playerId": DEUS_PLAYER_ID}).status_code == 404
    # and he does not show up as a neighbour (the game draws his card itself)
    info = client.get("/static/dragoncity/srv/get_player_info.json").get_data(as_text=True)
    assert str(DEUS_PLAYER_ID) not in info.split('"neighbors"')[1][:200]


def test_admins_cannot_edit_or_delete_deus(app, admin_client):
    make_deus()
    url = f"/api/admin/users/{DEUS_PLAYER_ID}"
    assert admin_client.patch(url, json={"isActive": True}).status_code == 403
    assert admin_client.delete(url).status_code == 403
    assert admin_client.post(f"{url}/friends", json={"friendId": 200000000}).status_code == 400
    assert admin_client.get(url).status_code == 200                # he can still be looked at
