from conftest import register


def test_cross_site_post_is_blocked(client, player):
    response = client.post("/api/auth/logout", headers={"Origin": "https://evil.example"})
    assert response.status_code == 403
    assert client.get("/api/auth/me").status_code == 200  # still logged in


def test_same_origin_post_is_allowed(client, player):
    response = client.post("/api/auth/logout", headers={"Origin": "http://localhost"})
    assert response.status_code == 200


def test_null_origin_is_blocked(client, player):
    assert client.post("/api/auth/logout", headers={"Origin": "null"}).status_code == 403


def test_game_packets_from_another_site_are_blocked(client, player):
    response = client.post("/static/dragoncity/srv/packet.php", data={"data": "{}"}, headers={"Origin": "https://evil.example"})
    assert response.status_code == 403
