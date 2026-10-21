from conftest import PASSWORD, register


def test_register_logs_in_with_httponly_cookie(client):
    response = register(client)
    assert response.status_code == 201
    cookie = response.headers["Set-Cookie"]
    assert "dc_session=" in cookie and "HttpOnly" in cookie and "SameSite=Lax" in cookie
    me = client.get("/api/auth/me")
    assert me.status_code == 200
    assert me.get_json()["user"]["email"] == "player@example.com"
    assert me.get_json()["user"]["isAdmin"] is False


def test_password_confirmation_must_match(client):
    response = client.post("/api/auth/register", json={
        "email": "a@example.com", "password": PASSWORD, "confirmPassword": PASSWORD + "x"})
    assert response.status_code == 400
    assert "confirmPassword" in response.get_json()["error"]["fields"]


def test_weak_or_invalid_input_is_rejected(client):
    short = client.post("/api/auth/register", json={"email": "a@example.com", "password": "short", "confirmPassword": "short"})
    assert short.status_code == 400 and "password" in short.get_json()["error"]["fields"]
    bad_email = client.post("/api/auth/register", json={"email": "nope", "password": PASSWORD, "confirmPassword": PASSWORD})
    assert bad_email.status_code == 400 and "email" in bad_email.get_json()["error"]["fields"]
    not_json = client.post("/api/auth/register", data="email=a", content_type="text/plain")
    assert not_json.status_code == 400


def test_cannot_self_assign_admin_on_register(client):
    response = client.post("/api/auth/register", json={
        "email": "a@example.com", "password": PASSWORD, "confirmPassword": PASSWORD, "isAdmin": True})
    assert response.status_code == 400


def test_duplicate_email_is_a_conflict_ignoring_case(client):
    assert register(client).status_code == 201
    other = client.application.test_client()
    assert register(other, email="PLAYER@example.com").status_code == 409


def test_login_errors_do_not_reveal_whether_the_email_exists(client):
    register(client)
    fresh = client.application.test_client()
    wrong_password = fresh.post("/api/auth/login", json={"email": "player@example.com", "password": "wrong-password"})
    unknown_email = fresh.post("/api/auth/login", json={"email": "nobody@example.com", "password": "wrong-password"})
    assert wrong_password.status_code == unknown_email.status_code == 401
    assert wrong_password.get_json() == unknown_email.get_json()


def test_login_is_case_insensitive_and_logout_ends_the_session(client):
    register(client)
    other = client.application.test_client()
    assert other.post("/api/auth/login", json={"email": "Player@Example.com", "password": PASSWORD}).status_code == 200
    assert other.get("/api/auth/me").status_code == 200
    assert other.post("/api/auth/logout").status_code == 200
    assert other.get("/api/auth/me").status_code == 401


def test_password_is_stored_hashed(client, player):
    from dragon_city.db.models import User
    from dragon_city.db.postgres import session_scope

    with session_scope() as session:
        user = session.get(User, player["id"])
        assert user.password_hash.startswith("$argon2id$") and PASSWORD not in user.password_hash


def test_login_is_rate_limited(client):
    register(client)
    other = client.application.test_client()
    statuses = [other.post("/api/auth/login", json={"email": "player@example.com", "password": "bad-password"}).status_code
                for _ in range(8)]
    assert 429 in statuses
