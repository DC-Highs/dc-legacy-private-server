"""set_resource_allies: stores a worker roster, never pays out gold or food on its own."""
from conftest import befriend, edit_save, load_save, packet

ALLIES_MARKET = 79
OTHER_BUILDING = 16  # a food farm: not a social building


def add_item(pid, iso, item_id):
    def mutate(d):
        d["map"]["items"][str(iso)] = [item_id, 5, 5, 0, 0, 1, {}]
    edit_save(pid, mutate)


def second_player(app, email="ally@example.com"):
    other = app.test_client()
    response = other.post("/api/auth/register", json={
        "email": email, "password": "correct horse battery", "confirmPassword": "correct horse battery",
    })
    assert response.status_code == 201
    return response.get_json()["user"]["id"]


def test_assigns_friends_as_workers(app, client, player):
    pid = player["id"]
    friend_id = second_player(app)
    befriend(pid, friend_id)
    add_item(pid, 50, ALLIES_MARKET)

    packet(client, ("set_resource_allies", [50, "[" + str(friend_id) + "]"]))

    item = load_save(pid)["map"]["items"]["50"]
    assert item[6]["allies"] == [friend_id]


def test_rejects_a_worker_who_is_not_a_friend(app, client, player):
    pid = player["id"]
    stranger_id = second_player(app, "stranger@example.com")
    add_item(pid, 50, ALLIES_MARKET)
    before = load_save(pid)

    packet(client, ("set_resource_allies", [50, "[" + str(stranger_id) + "]"]))

    assert load_save(pid) == before  # rejected, nothing stored


def test_rejects_a_building_that_is_not_the_allies_market(client, player):
    pid = player["id"]
    add_item(pid, 51, OTHER_BUILDING)
    before = load_save(pid)

    packet(client, ("set_resource_allies", [51, "[]"]))

    assert load_save(pid) == before


def test_rejects_more_workers_than_slots(app, client, player):
    from src.auth import service
    from src.db.postgres import session_scope

    pid = player["id"]
    friend_ids = []
    with session_scope() as session:
        for i in range(7):
            user = service.create_user(session, f"ally{i}@example.com", "correct horse battery")
            friend_ids.append(user.id)
    for fid in friend_ids:
        befriend(pid, fid)
    add_item(pid, 50, ALLIES_MARKET)

    packet(client, ("set_resource_allies", [50, str(friend_ids).replace("'", "")]))

    item = load_save(pid)["map"]["items"]["50"]
    assert len(item) <= 6 or "allies" not in item[6]


def test_does_not_grant_any_resources(app, client, player):
    pid = player["id"]
    friend_id = second_player(app)
    befriend(pid, friend_id)
    add_item(pid, 50, ALLIES_MARKET)
    before = load_save(pid)["playerInfo"]

    packet(client, ("set_resource_allies", [50, "[" + str(friend_id) + "]"]))

    after = load_save(pid)["playerInfo"]
    assert after == before


def test_can_be_cleared_by_sending_an_empty_list(app, client, player):
    pid = player["id"]
    friend_id = second_player(app)
    befriend(pid, friend_id)
    add_item(pid, 50, ALLIES_MARKET)
    packet(client, ("set_resource_allies", [50, "[" + str(friend_id) + "]"]))

    packet(client, ("set_resource_allies", [50, "[]"]))

    item = load_save(pid)["map"]["items"]["50"]
    assert item[6]["allies"] == []
