import pytest

from dragon_city.config import get_settings


@pytest.fixture()
def dist(tmp_path, monkeypatch):
    (tmp_path / "dist" / "_app").mkdir(parents=True)
    (tmp_path / "dist" / "index.html").write_text("<html>client</html>")
    (tmp_path / "dist" / "_app" / "main.js").write_text("console.log(1)")
    (tmp_path / "secret.txt").write_text("secret")
    monkeypatch.setenv("FRONTEND_DIST", str(tmp_path / "dist"))
    get_settings.cache_clear()
    yield tmp_path
    get_settings.cache_clear()


def test_health_checks_both_databases(client):
    assert client.get("/api/game/health").get_json() == {"status": "ok"}


def test_the_web_client_is_served_with_a_history_fallback(client, dist):
    assert b"client" in client.get("/").data
    assert b"client" in client.get("/admin").data          # client-side route
    assert client.get("/_app/main.js").data == b"console.log(1)"
    assert client.get("/missing.js").status_code == 404    # a file, not a page


def test_the_web_client_cannot_read_outside_its_folder(client, dist):
    assert b"secret" not in client.get("/%2e%2e/secret.txt").data
    assert b"secret" not in client.get("/../secret.txt").data


def test_unknown_api_paths_are_json_404s_not_the_web_client(client, dist):
    response = client.get("/api/nope")
    assert response.status_code == 404 and response.is_json
    assert client.get("/flash/x.swf").status_code in (401, 404)


def test_a_missing_build_is_reported(client, tmp_path, monkeypatch):
    monkeypatch.setenv("FRONTEND_DIST", str(tmp_path / "nothing"))
    get_settings.cache_clear()
    assert client.get("/").status_code == 503
    get_settings.cache_clear()


def test_security_headers_are_set(client, player):
    response = client.get("/api/auth/me")
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["Cache-Control"] == "no-store"
