import pytest

from src.config import get_settings


@pytest.fixture()
def versions_dir(tmp_path, monkeypatch):
    folder = tmp_path / "versions"
    folder.mkdir()
    (tmp_path / "DCLoader.swf").write_bytes(b"FWS")
    for name in ("Base_sec_0.6.7c.swf", "Base_sec_0.10.0.swf", "Base_sec_0.7.9.swf", "Base_sec_0.6.7c - Flashpoint.swf"):
        (folder / name).write_bytes(b"FWS")
    (folder / "notes.txt").write_text("x")
    monkeypatch.setenv("FLASH_DIR", str(tmp_path))
    get_settings.cache_clear()
    yield folder
    get_settings.cache_clear()


def swf_to_load(client):
    return client.get("/api/game/bootstrap").get_json()["flashVars"]["swftoload"]


def test_admin_lists_the_versions_in_the_folder(admin_client, versions_dir):
    data = admin_client.get("/api/admin/game-version").get_json()
    # files with spaces and non-SWF files are not versions; ordering is numeric
    assert [v["file"] for v in data["versions"]] == ["Base_sec_0.6.7c.swf", "Base_sec_0.7.9.swf", "Base_sec_0.10.0.swf"]
    assert data["versions"][0]["version"] == "0.6.7c"
    assert data["selected"] == data["default"] == "Base_sec_0.6.7c.swf"


def test_selected_version_is_what_the_game_loads(app, admin_client, versions_dir):
    response = admin_client.put("/api/admin/game-version", json={"file": "Base_sec_0.7.9.swf"})
    assert response.status_code == 200 and response.get_json()["selected"] == "Base_sec_0.7.9.swf"
    assert swf_to_load(admin_client) == "flash/versions/Base_sec_0.7.9.swf"

    other = app.test_client()
    other.post("/api/auth/register", json={"email": "p@example.com", "password": "correct horse battery", "confirmPassword": "correct horse battery"})
    assert swf_to_load(other) == "flash/versions/Base_sec_0.7.9.swf"


def test_unknown_versions_are_refused(admin_client, versions_dir):
    for name in ("Base_sec_9.9.9.swf", "DCLoader.swf", "../secret.swf", "Base_sec_0.6.7c - Flashpoint.swf"):
        assert admin_client.put("/api/admin/game-version", json={"file": name}).status_code == 400
    assert admin_client.get("/api/admin/game-version").get_json()["selected"] == "Base_sec_0.6.7c.swf"


def test_a_removed_version_falls_back_to_the_default(admin_client, versions_dir):
    admin_client.put("/api/admin/game-version", json={"file": "Base_sec_0.7.9.swf"})
    (versions_dir / "Base_sec_0.7.9.swf").unlink()
    assert swf_to_load(admin_client) == "flash/versions/Base_sec_0.6.7c.swf"


def test_only_admins_choose_the_version(client, player, versions_dir):
    assert client.get("/api/admin/game-version").status_code == 403
    assert client.put("/api/admin/game-version", json={"file": "Base_sec_0.7.9.swf"}).status_code == 403
