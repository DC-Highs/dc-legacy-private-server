"""mistery_egg_hatch: the reward comes from the game config's weighted table, never the client."""
from conftest import edit_save, load_save, packet
from src import storage

SMALL_MISTERY_EGG = 154
NORMAL_DRAGON_EGG = 1000


def add_egg(pid, egg_uid, item_id):
    def mutate(d):
        d["map"]["eggs"].append({"id": egg_uid, "type": item_id, "name": "Egg", "xp": 0, "hatched": False, "ts": 0})
    edit_save(pid, mutate)


def tier_table(tier):
    return storage.load_base_config()["mistery_egg"][tier]


def test_hatching_gives_exactly_one_of_the_tiers_configured_rewards(client, player):
    pid = player["id"]
    add_egg(pid, 9001, SMALL_MISTERY_EGG)
    before = load_save(pid)["playerInfo"]

    packet(client, ("mistery_egg_hatch", [9001]))

    save = load_save(pid)
    assert all(e["id"] != 9001 for e in save["map"]["eggs"])              # the egg is consumed

    rewards = tier_table("SMALL")["rewards"]
    dragon_ids = [r for r in rewards if isinstance(r, int)]
    resource_rewards = [r for r in rewards if isinstance(r, dict)]
    after = save["playerInfo"]

    gained_dragon = any(d.get("iid") in dragon_ids for d in save["map"]["store"]["dragons"])
    gained_resources = any(
        after["gold"] - before["gold"] == r.get("g", 0) and after["food"] - before["food"] == r.get("f", 0)
        for r in resource_rewards
    )
    assert gained_dragon or gained_resources


def test_hatching_rejects_an_unknown_egg(client, player):
    packet(client, ("mistery_egg_hatch", [12345]))
    assert load_save(player["id"])["map"]["store"]["dragons"] == []


def test_hatching_rejects_a_normal_dragon_egg(client, player):
    pid = player["id"]
    add_egg(pid, 9002, NORMAL_DRAGON_EGG)

    packet(client, ("mistery_egg_hatch", [9002]))

    save = load_save(pid)
    assert any(e["id"] == 9002 for e in save["map"]["eggs"])              # untouched, not consumed
    assert save["map"]["store"]["dragons"] == []


def test_the_same_egg_cannot_be_hatched_twice(client, player):
    pid = player["id"]
    add_egg(pid, 9003, SMALL_MISTERY_EGG)

    packet(client, ("mistery_egg_hatch", [9003]))
    after_first = load_save(pid)

    packet(client, ("mistery_egg_hatch", [9003]))                        # the egg is gone now
    assert load_save(pid) == after_first
