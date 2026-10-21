import pytest

from conftest import load_save, register
from src import friends
from src.db.models import Friendship
from src.extensions import limiter
from src.db.postgres import session_scope


def make_player(app, email):
    limiter.reset()                      # sign-up is rate limited; these tests create many players
    client = app.test_client()
    response = register(client, email=email)
    assert response.status_code == 201
    return client, response.get_json()["user"]["id"]


def gems(player_id):
    return load_save(player_id)["playerInfo"]["cash"]


@pytest.fixture()
def pair(app):
    alice, alice_id = make_player(app, "alice@example.com")
    bob, bob_id = make_player(app, "bob@example.com")
    return alice, alice_id, bob, bob_id


def overview(client):
    return client.get("/api/friends").get_json()


def ask(client, player_id):
    return client.post("/api/friends/requests", json={"playerId": player_id})


# --- the flow ---------------------------------------------------------------------


def test_a_request_is_sent_seen_and_accepted(pair):
    alice, alice_id, bob, bob_id = pair
    response = ask(alice, bob_id)
    assert response.status_code == 201 and response.get_json()["accepted"] is False

    sent, received = overview(alice), overview(bob)
    assert sent["outgoing"][0]["to"]["id"] == bob_id and sent["incoming"] == []
    assert received["incoming"][0]["from"]["id"] == alice_id
    assert bob.get("/api/friends/summary").get_json() == {"incoming": 1}
    assert alice.get("/api/friends/summary").get_json() == {"incoming": 0}

    request_id = received["incoming"][0]["requestId"]
    accepted = bob.post(f"/api/friends/requests/{request_id}/accept")
    assert accepted.status_code == 200 and accepted.get_json()["gemsAwarded"] == 5

    assert [f["id"] for f in overview(alice)["friends"]] == [bob_id]
    assert [f["id"] for f in overview(bob)["friends"]] == [alice_id]
    assert overview(bob)["incoming"] == [] and overview(alice)["outgoing"] == []


def test_neighbours_appear_in_the_game_once_accepted(pair):
    alice, alice_id, bob, bob_id = pair
    ask(alice, bob_id)
    info = alice.get("/static/dragoncity/srv/get_player_info.json").get_data(as_text=True)
    assert '"neighbors":[]' in info.replace(" ", "")          # pending is not a neighbour yet

    bob.post(f"/api/friends/requests/{overview(bob)['incoming'][0]['requestId']}/accept")
    info = alice.get("/static/dragoncity/srv/get_player_info.json").get_data(as_text=True)
    assert f'"pid":"{bob_id}"' in info.replace(" ", "")
    assert alice.get("/api/game/bootstrap").get_json()["flashVars"]["fb_sig_friends"] == str(bob_id)


def test_only_the_addressee_can_answer_a_request(app, pair):
    alice, alice_id, bob, bob_id = pair
    carol, _ = make_player(app, "carol@example.com")
    ask(alice, bob_id)
    request_id = overview(bob)["incoming"][0]["requestId"]

    assert alice.post(f"/api/friends/requests/{request_id}/accept").status_code == 404      # the requester
    assert carol.post(f"/api/friends/requests/{request_id}/accept").status_code == 404      # a stranger
    assert carol.post(f"/api/friends/requests/{request_id}/decline").status_code == 404
    assert carol.delete(f"/api/friends/requests/{request_id}").status_code == 404
    assert bob.delete(f"/api/friends/requests/{request_id}").status_code == 404             # only the sender cancels
    assert overview(bob)["friends"] == []


def test_declining_and_cancelling(pair):
    alice, alice_id, bob, bob_id = pair
    ask(alice, bob_id)
    request_id = overview(bob)["incoming"][0]["requestId"]
    assert bob.post(f"/api/friends/requests/{request_id}/decline").status_code == 200
    assert overview(bob)["incoming"] == [] and overview(alice)["outgoing"] == []
    assert bob.post(f"/api/friends/requests/{request_id}/accept").status_code == 404        # already answered

    # the sender cannot ask again right away
    assert ask(alice, bob_id).status_code == 429
    # but the other person can ask them
    assert ask(bob, alice_id).status_code == 201

    # and a sender can take a pending request back
    carol_request = overview(alice)["incoming"][0]["requestId"]
    assert bob.delete(f"/api/friends/requests/{carol_request}").status_code == 200
    assert overview(alice)["incoming"] == []


def test_a_declined_request_can_be_sent_again_after_the_cooldown(pair):
    alice, alice_id, bob, bob_id = pair
    ask(alice, bob_id)
    bob.post(f"/api/friends/requests/{overview(bob)['incoming'][0]['requestId']}/decline")
    with session_scope() as session:
        row = session.query(Friendship).one()
        from datetime import timedelta
        row.responded_at = row.responded_at - friends.DECLINE_COOLDOWN - timedelta(hours=1)
    assert ask(alice, bob_id).status_code == 201


def test_requests_that_meet_become_a_friendship(pair):
    alice, alice_id, bob, bob_id = pair
    ask(alice, bob_id)
    response = ask(bob, alice_id)                  # Bob had a request from Alice: accept instead
    assert response.status_code == 201 and response.get_json()["accepted"] is True
    assert response.get_json()["gemsAwarded"] == 5
    assert [f["id"] for f in overview(alice)["friends"]] == [bob_id]


def test_requests_are_validated(app, pair):
    alice, alice_id, bob, bob_id = pair
    assert ask(alice, alice_id).status_code == 400                                       # yourself
    assert ask(alice, 999999999).status_code == 404                                      # unknown
    assert alice.post("/api/friends/requests", json={"playerId": "x"}).status_code == 400
    assert alice.post("/api/friends/requests", json={"playerId": bob_id, "extra": 1}).status_code == 400
    assert alice.post("/api/friends/requests", json={}).status_code == 400

    assert ask(alice, bob_id).status_code == 201
    assert ask(alice, bob_id).status_code == 409                                         # already sent


def test_a_friend_cannot_be_asked_again_and_can_be_removed(pair):
    alice, alice_id, bob, bob_id = pair
    ask(alice, bob_id)
    bob.post(f"/api/friends/requests/{overview(bob)['incoming'][0]['requestId']}/accept")
    assert ask(alice, bob_id).status_code == 409
    assert ask(bob, alice_id).status_code == 409

    assert bob.delete(f"/api/friends/{alice_id}").status_code == 200
    assert overview(alice)["friends"] == [] and overview(bob)["friends"] == []
    assert bob.delete(f"/api/friends/{alice_id}").status_code == 404
    assert alice.get(f"/static/dragoncity/srv/get_player_info.json?user={bob_id}").status_code == 404   # no more visits


def test_disabled_accounts_cannot_be_asked(app, pair, admin_client):
    alice, alice_id, bob, bob_id = pair
    admin_client.patch(f"/api/admin/users/{bob_id}", json={"isActive": False})
    assert ask(alice, bob_id).status_code == 404


def test_the_friends_api_never_shows_emails(pair):
    alice, alice_id, bob, bob_id = pair
    ask(alice, bob_id)
    assert "bob@example.com" not in alice.get("/api/friends").get_data(as_text=True)
    assert "alice@example.com" not in bob.get("/api/friends").get_data(as_text=True)


def test_the_friends_api_requires_a_login(client):
    for method, path in (("get", "/api/friends"), ("get", "/api/friends/summary"),
                         ("post", "/api/friends/requests"), ("post", "/api/friends/requests/1/accept"),
                         ("delete", "/api/friends/1")):
        assert getattr(client, method)(path).status_code == 401


def test_sending_requests_is_rate_limited(app, pair):
    alice, alice_id, bob, bob_id = pair
    statuses = [ask(alice, 900000000 + i).status_code for i in range(14)]
    assert 429 in statuses


def test_limits_on_pending_requests_and_friend_lists(app, pair, monkeypatch):
    alice, alice_id, bob, bob_id = pair
    monkeypatch.setattr(friends, "MAX_FRIENDS", 1)
    carol, carol_id = make_player(app, "carol@example.com")
    ask(alice, bob_id)
    bob.post(f"/api/friends/requests/{overview(bob)['incoming'][0]['requestId']}/accept")
    assert ask(alice, carol_id).status_code == 409                    # Alice's list is full
    assert ask(carol, bob_id).status_code == 201                      # Bob's list is full too:
    request_id = overview(bob)["incoming"][0]["requestId"]
    assert bob.post(f"/api/friends/requests/{request_id}/accept").status_code == 409   # it cannot be accepted


# --- the "add a friend and get 5 gems" reward ------------------------------------------


def test_both_players_get_5_gems_for_a_new_friend(pair):
    alice, alice_id, bob, bob_id = pair
    start_alice, start_bob = gems(alice_id), gems(bob_id)
    ask(alice, bob_id)
    assert gems(alice_id) == start_alice and gems(bob_id) == start_bob        # nothing for a request
    bob.post(f"/api/friends/requests/{overview(bob)['incoming'][0]['requestId']}/accept")
    assert gems(alice_id) == start_alice + 5 and gems(bob_id) == start_bob + 5


def test_a_friend_pays_only_once(pair):
    alice, alice_id, bob, bob_id = pair
    start = gems(alice_id)
    ask(alice, bob_id)
    bob.post(f"/api/friends/requests/{overview(bob)['incoming'][0]['requestId']}/accept")
    bob.delete(f"/api/friends/{alice_id}")
    ask(alice, bob_id)
    bob.post(f"/api/friends/requests/{overview(bob)['incoming'][0]['requestId']}/accept")
    assert gems(alice_id) == start + 5                                       # not 10


def test_only_the_first_five_friends_pay(app):
    main, main_id = make_player(app, "main@example.com")
    start = gems(main_id)
    for i in range(7):
        other, other_id = make_player(app, f"p{i}@example.com")
        ask(other, main_id)
        main.post(f"/api/friends/requests/{overview(main)['incoming'][0]['requestId']}/accept")
    assert gems(main_id) == start + 5 * friends.FRIEND_REWARD_LIMIT
    assert len(overview(main)["friends"]) == 7


def test_friendships_made_by_an_admin_also_pay(app, pair, admin_client):
    alice, alice_id, bob, bob_id = pair
    start = gems(alice_id)
    assert admin_client.post(f"/api/admin/users/{alice_id}/friends", json={"friendId": bob_id}).status_code == 201
    assert gems(alice_id) == start + 5


def test_an_admin_can_accept_a_pending_request_by_adding_the_friend(app, pair, admin_client):
    alice, alice_id, bob, bob_id = pair
    ask(alice, bob_id)
    assert admin_client.post(f"/api/admin/users/{alice_id}/friends", json={"friendId": bob_id}).status_code == 201
    assert overview(bob)["incoming"] == [] and [f["id"] for f in overview(bob)["friends"]] == [alice_id]
