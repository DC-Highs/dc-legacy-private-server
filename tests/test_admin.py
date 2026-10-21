from conftest import PASSWORD, load_save


def test_admin_api_requires_an_admin(client, player, admin_client):
    assert client.get("/api/admin/users").status_code == 403
    anonymous = client.application.test_client()
    assert anonymous.get("/api/admin/users").status_code == 401
    assert admin_client.get("/api/admin/users").status_code == 200


def test_admin_can_create_list_search_and_inspect_users(admin_client):
    created = admin_client.post("/api/admin/users", json={"email": "New@Example.com", "password": PASSWORD})
    assert created.status_code == 201
    user = created.get_json()["user"]
    assert user["email"] == "new@example.com" and user["isAdmin"] is False and user["player"]["gold"] > 0

    listing = admin_client.get("/api/admin/users?query=new@").get_json()
    assert listing["total"] == 1 and listing["items"][0]["id"] == user["id"]
    assert admin_client.get(f"/api/admin/users?query={user['id']}").get_json()["total"] == 1
    assert admin_client.get(f"/api/admin/users/{user['id']}").status_code == 200
    # LIKE wildcards in the search are matched literally
    assert admin_client.get("/api/admin/users?query=%25").get_json()["total"] == 0


def test_admin_creation_rejects_duplicates_and_weak_passwords(admin_client):
    assert admin_client.post("/api/admin/users", json={"email": "a@example.com", "password": "short"}).status_code == 400
    assert admin_client.post("/api/admin/users", json={"email": "admin@example.com", "password": PASSWORD}).status_code == 409


def test_disabling_or_changing_password_ends_the_users_sessions(app, admin_client, player, client):
    assert client.get("/api/auth/me").status_code == 200
    assert admin_client.patch(f"/api/admin/users/{player['id']}", json={"isActive": False}).status_code == 200
    assert client.get("/api/auth/me").status_code == 401
    other = app.test_client()
    assert other.post("/api/auth/login", json={"email": "player@example.com", "password": PASSWORD}).status_code == 403

    new_password = "another long password"
    admin_client.patch(f"/api/admin/users/{player['id']}", json={"isActive": True, "password": new_password})
    assert other.post("/api/auth/login", json={"email": "player@example.com", "password": PASSWORD}).status_code == 401
    assert other.post("/api/auth/login", json={"email": "player@example.com", "password": new_password}).status_code == 200


def test_admin_cannot_lock_themselves_out(admin_client):
    me = admin_client.get("/api/auth/me").get_json()["user"]["id"]
    assert admin_client.patch(f"/api/admin/users/{me}", json={"isAdmin": False}).status_code == 403
    assert admin_client.patch(f"/api/admin/users/{me}", json={"isActive": False}).status_code == 403
    assert admin_client.delete(f"/api/admin/users/{me}").status_code == 403


def test_deleting_a_user_removes_account_and_save(admin_client, player, client):
    assert admin_client.delete(f"/api/admin/users/{player['id']}").status_code == 200
    assert admin_client.get(f"/api/admin/users/{player['id']}").status_code == 404
    assert load_save(player["id"]) is None
    assert client.get("/api/auth/me").status_code == 401


def test_admin_can_edit_resources_and_reset_the_save(admin_client, player):
    url = f"/api/admin/users/{player['id']}/resources"
    assert admin_client.patch(url, json={"gold": 123, "cash": 7}).status_code == 200
    assert load_save(player["id"])["playerInfo"]["gold"] == 123
    assert admin_client.patch(url, json={"gold": -1}).status_code == 400
    assert admin_client.patch(url, json={"gold": 10 ** 12}).status_code == 400
    assert admin_client.patch(url, json={}).status_code == 400

    assert admin_client.post(f"/api/admin/users/{player['id']}/reset-player").status_code == 200
    assert load_save(player["id"])["playerInfo"]["gold"] != 123


def test_admin_cannot_set_unknown_fields(admin_client, player):
    assert admin_client.patch(f"/api/admin/users/{player['id']}", json={"id": 1}).status_code == 400
