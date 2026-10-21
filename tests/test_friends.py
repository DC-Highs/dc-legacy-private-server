import json

from conftest import PASSWORD, befriend, load_save, packet, register


def other_player(app, email="friend@example.com"):
    client = app.test_client()
    response = register(client, email=email)
    assert response.status_code == 201
    return client, response.get_json()["user"]["id"]


def player_info(client, **query):
    suffix = "?" + "&".join(f"{k}={v}" for k, v in query.items()) if query else ""
    response = client.get("/static/dragoncity/srv/get_player_info.json" + suffix)
    return response, (json.loads(response.get_data(as_text=True).split(";", 1)[1]) if response.status_code == 200 else None)


def test_a_new_player_has_no_neighbours(client, player):
    _, info = player_info(client)
    assert info["neighbors"] == []
    assert client.get("/api/game/bootstrap").get_json()["flashVars"]["fb_sig_friends"] == ""


def test_friends_appear_as_neighbours_in_the_game(app, client, player):
    friend_client, friend_id = other_player(app)
    befriend(player["id"], friend_id)

    _, info = player_info(client)
    assert info["neighbors"] == [{"pid": str(friend_id), "name": "friend", "xp": 0, "level": 1, "world_id": 0}]
    assert client.get("/api/game/bootstrap").get_json()["flashVars"]["fb_sig_friends"] == str(friend_id)
    # friendship is mutual
    _, friend_info = player_info(friend_client)
    assert friend_info["neighbors"][0]["pid"] == str(player["id"])
    # the list is not stored in the save
    assert load_save(player["id"])["neighbors"] == []


def test_neighbours_show_their_current_level_and_xp(app, client, player):
    friend_client, friend_id = other_player(app)
    befriend(player["id"], friend_id)
    packet(friend_client, ("buy", ["700", 16, 3, 3, 0, 0, 1]))
    _, info = player_info(client)
    assert info["neighbors"][0]["xp"] == 100


def test_only_friends_can_be_visited(app, client, player):
    friend_client, friend_id = other_player(app)
    stranger_response, _ = player_info(client, user=friend_id)
    assert stranger_response.status_code == 404

    befriend(player["id"], friend_id)
    visit, visited = player_info(client, user=friend_id)
    assert visit.status_code == 200 and visited["playerInfo"]["pid"] == str(friend_id)


def test_only_friends_can_be_assisted(app, client, player):
    friend_client, friend_id = other_player(app)
    packet(client, ("assist_neighbor", [friend_id, "[1,2]"]))
    packet(friend_client, ("ping",))
    assert "assistRewardsLeft" not in load_save(friend_id)["privateState"]

    befriend(player["id"], friend_id)
    packet(client, ("assist_neighbor", [friend_id, "[1,2]"]))
    packet(friend_client, ("ping",))
    assert load_save(friend_id)["privateState"]["assistRewardsLeft"] == 2


def test_admin_manages_friendships(app, admin_client, player, client):
    _, friend_id = other_player(app)
    url = f"/api/admin/users/{player['id']}/friends"

    assert admin_client.get(url).get_json() == {"items": []}
    added = admin_client.post(url, json={"friendId": friend_id})
    assert added.status_code == 201 and added.get_json()["items"][0]["id"] == friend_id
    assert admin_client.get(f"/api/admin/users/{friend_id}/friends").get_json()["items"][0]["id"] == player["id"]

    assert admin_client.post(url, json={"friendId": friend_id}).status_code == 409           # duplicate
    assert admin_client.post(f"/api/admin/users/{friend_id}/friends", json={"friendId": player["id"]}).status_code == 409
    assert admin_client.post(url, json={"friendId": player["id"]}).status_code == 400        # itself
    assert admin_client.post(url, json={"friendId": 999999999}).status_code == 404           # unknown
    assert admin_client.post(url, json={"friendId": "x"}).status_code == 400
    assert admin_client.post(url, json={"friendId": friend_id, "extra": 1}).status_code == 400

    assert admin_client.delete(f"{url}/{friend_id}").status_code == 200
    assert admin_client.delete(f"{url}/{friend_id}").status_code == 404
    assert admin_client.get(url).get_json() == {"items": []}


def test_friendship_endpoints_are_admin_only(app, client, player):
    _, friend_id = other_player(app)
    assert client.post(f"/api/admin/users/{player['id']}/friends", json={"friendId": friend_id}).status_code == 403
    assert client.get(f"/api/admin/users/{player['id']}/friends").status_code == 403


def test_deleting_an_account_removes_its_friendships(app, admin_client, player):
    _, friend_id = other_player(app)
    befriend(player["id"], friend_id)
    admin_client.delete(f"/api/admin/users/{player['id']}")
    assert admin_client.get(f"/api/admin/users/{friend_id}/friends").get_json() == {"items": []}
