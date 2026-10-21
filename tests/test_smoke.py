from conftest import load_save, packet


def test_register_creates_save_and_packet_works(client, player):
    save = load_save(player["id"])
    assert save["playerInfo"]["pid"] == str(player["id"])
    results = packet(client, ("ping",))
    assert results[0]["cmd"] == "ping" and results[0]["result"] == "ok"
