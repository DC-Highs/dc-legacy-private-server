"""The client is untrusted: every way of injecting resources or breaking the save must fail."""
import json
import time

from conftest import PASSWORD, edit_save, load_save, packet, register

FARM = 16          # food farm, costs 100 gold, no build time
HABITAT = 24       # needs level 7, builds in an hour
DRAGON = 1000      # costs 15000 gold


def gold(pid):
    return load_save(pid)["playerInfo"]["gold"]


def info(pid):
    return load_save(pid)["playerInfo"]


def give(pid, **resources):
    edit_save(pid, lambda d: d["playerInfo"].update(resources))


def add_item(pid, iso, item_id, attrs=None, **extra):
    def mutate(d):
        d["map"]["items"][str(iso)] = [item_id, 5, 5, 0, 0, 1, attrs if attrs is not None else {}]
        d["map"].update(extra)
    edit_save(pid, mutate)


def second_player(app, email="other@example.com"):
    other = app.test_client()
    response = register(other, email=email)
    assert response.status_code == 201
    return other, response.get_json()["user"]["id"]


# --- identity -------------------------------------------------------------------


def test_game_endpoints_require_a_login(client):
    assert client.post("/static/dragoncity/srv/packet.php", data={"data": "{}"}).status_code == 401
    assert client.get("/static/dragoncity/srv/get_player_info.json").status_code == 401
    assert client.get("/static/dragoncity/srv/get_game_config.json").status_code == 401
    assert client.get("/flash/DCLoader.swf").status_code == 401
    assert client.get("/stream").status_code == 401


def test_the_userid_sent_by_the_client_is_ignored(app, client, player):
    other, other_id = second_player(app)
    give(other_id, gold=5000)
    give(player["id"], gold=5000)

    payload = "sig;" + json.dumps({"commands": [{"cmd": "buy", "args": ["700", FARM, 3, 3, 0, 0, 1], "number": 1}]})
    response = client.post(f"/static/dragoncity/srv/packet.php?USERID={other_id}",
                           data={"data": payload, "id": str(other_id)})
    assert response.status_code == 200
    assert gold(other_id) == 5000            # the victim is untouched
    assert gold(player["id"]) == 4900        # the acting account paid


def test_visiting_an_unknown_neighbour_does_not_create_a_save(client, player):
    response = client.get("/static/dragoncity/srv/get_player_info.json?user=999999999")
    assert response.status_code == 404
    from dragon_city import storage
    assert not storage.player_exists(999999999)


def test_visiting_a_real_neighbour_is_read_only(app, client, player):
    other, other_id = second_player(app)
    before = load_save(other_id)
    response = client.get(f"/static/dragoncity/srv/get_player_info.json?user={other_id}")
    assert response.status_code == 200
    assert load_save(other_id)["playerInfo"] == before["playerInfo"]


# --- buying ----------------------------------------------------------------------


def test_buy_needs_the_money_and_a_free_slot(client, player):
    give(player["id"], gold=50)
    packet(client, ("buy", ["700", FARM, 3, 3, 0, 0, 1]))
    assert "700" not in load_save(player["id"])["map"]["items"] and gold(player["id"]) == 50

    give(player["id"], gold=1000)
    packet(client, ("buy", ["700", FARM, 3, 3, 0, 0, 1]))
    assert "700" in load_save(player["id"])["map"]["items"] and gold(player["id"]) == 900

    packet(client, ("buy", ["700", FARM, 9, 9, 0, 0, 1]))     # same iso id again
    assert gold(player["id"]) == 900


def test_free_or_unsellable_items_cannot_be_bought(client, player):
    from dragon_city import storage
    free_item = next(i["id"] for i in storage.load_base_config()["items"] if not i.get("costs") and i["group_type"] != "DRAGON")
    give(player["id"], gold=10 ** 6)
    packet(client, ("buy", ["701", free_item, 3, 3, 0, 0, 1]), ("buy", ["702", DRAGON, 3, 3, 0, 0, 1]))
    items = load_save(player["id"])["map"]["items"]
    assert "701" not in items and "702" not in items and gold(player["id"]) == 10 ** 6


def test_level_requirements_are_enforced(client, player):
    give(player["id"], gold=10 ** 6)
    packet(client, ("buy", ["703", HABITAT, 3, 3, 0, 0, 1]))
    assert "703" not in load_save(player["id"])["map"]["items"]
    give(player["id"], level=7)
    packet(client, ("buy", ["703", HABITAT, 3, 3, 0, 0, 1]))
    assert "703" in load_save(player["id"])["map"]["items"]


def test_buy_egg_checks_funds_and_that_the_item_is_a_dragon(client, player):
    give(player["id"], gold=100)
    packet(client, ("buy_egg", [5001, DRAGON]))
    assert load_save(player["id"])["map"]["eggs"] == []
    give(player["id"], gold=20000)
    packet(client, ("buy_egg", [5001, DRAGON]), ("buy_egg", [5001, DRAGON]), ("buy_egg", [5002, FARM]))
    eggs = load_save(player["id"])["map"]["eggs"]
    assert [e["id"] for e in eggs] == [5001] and gold(player["id"]) == 5000


# --- numbers and sizes ------------------------------------------------------------


def test_absurd_numbers_are_rejected_and_do_not_poison_the_save(client, player):
    give(player["id"], gold=10 ** 6)
    packet(client, ("buy", ["704", FARM, 10 ** 30, 3, 0, 0, 1]),
           ("buy", ["705", FARM, -5, 3, 0, 0, 1]),
           ("buy", ["706", FARM, "3; DROP TABLE", 3, 0, 0, 1]),
           ("buy", [True, FARM, 3, 3, 0, 0, 1]),
           ("buy", ["707", FARM, {"$gt": 1}, 3, 0, 0, 1]))
    assert gold(player["id"]) == 10 ** 6
    assert packet(client, ("ping",))[0]["result"] == "ok"      # the save still loads and saves


def test_huge_indexes_cannot_bloat_the_save(client, player):
    packet(client, ("set_goals", [10 ** 9, "[1]"]), ("set_goals", [5, "[1]"]), ("start_training", ["1", 1, 1, 10 ** 6]))
    goals = load_save(player["id"])["privateState"]["goals"]
    assert len(goals) < 1000


def test_nan_and_oversized_packets_are_refused(client, player):
    assert client.post("/static/dragoncity/srv/packet.php", data={"data": '{"commands": [NaN]}'}).status_code == 400
    assert client.post("/static/dragoncity/srv/packet.php", data={"data": "not json"}).status_code == 400
    assert client.post("/static/dragoncity/srv/packet.php", data={"data": "x" * 300_000}).status_code == 413


def test_a_packet_is_capped_to_200_commands(client, player):
    give(player["id"], gold=10 ** 6)
    commands = [("sell_egg", [i]) for i in range(1000)]
    assert len(packet(client, *commands)) == 200


def test_a_failing_command_leaves_no_partial_changes(client, player, monkeypatch):
    from dragon_city.commands import base
    from dragon_city.enums import Command

    def half_done(ctx):
        ctx.info["gold"] = 1
        raise RuntimeError("boom")

    monkeypatch.setitem(base._handlers, Command.PING, half_done)
    give(player["id"], gold=777)
    assert packet(client, ("ping",))[0]["result"] == "ok"
    assert gold(player["id"]) == 777


# --- rewards that must not repeat -------------------------------------------------


def test_levels_go_up_one_at_a_time(client, player):
    give(player["id"], xp=10 ** 6)
    packet(client, ("level_up", [10]))
    assert info(player["id"])["level"] == 1
    packet(client, ("level_up", [2]), ("level_up", [2]), ("level_up", [4]))
    assert info(player["id"])["level"] == 2


def test_a_level_needs_its_experience(client, player):
    cash = info(player["id"])["cash"]
    packet(client, ("level_up", [2]))                 # level 2 needs 200 xp
    assert info(player["id"])["level"] == 1 and info(player["id"])["cash"] == cash
    give(player["id"], xp=200)
    packet(client, ("level_up", [2]))
    assert info(player["id"])["level"] == 2 and info(player["id"])["cash"] == cash + 1


def test_a_goal_pays_out_once(client, player):
    before = gold(player["id"])
    packet(client, ("complete_goal", [2]))
    after_first = gold(player["id"])
    assert after_first > before
    packet(client, ("complete_goal", [2]), ("complete_goal", [2]))
    assert gold(player["id"]) == after_first


def test_building_xp_is_paid_once(client, player):
    add_item(player["id"], 800, 9, {"tb": int(time.time()) + 100})   # a building under construction
    packet(client, ("finish_building", [800, 0]))
    xp = info(player["id"])["xp"]
    assert xp > 0
    packet(client, ("finish_building", [800, 0]), ("finish_building", [800, 0]))
    assert info(player["id"])["xp"] == xp


def test_the_weekly_reward_is_claimed_once_per_week(client, player):
    packet(client, ("weekly_reward", ["[0]"]))
    after_first = gold(player["id"])
    packet(client, ("weekly_reward", ["[0]"]))
    assert gold(player["id"]) == after_first


def test_free_card_draws_are_limited(client, player):
    first = packet(client, ("deus_cards_generate", [0, 0]))[0]["result"]
    assert isinstance(first, int)
    second = packet(client, ("deus_cards_generate", [0, 0]))[0]["result"]
    assert second == "ok" and load_save(player["id"])["privateState"]["deus_cards"]["pending_prize"] == first
    packet(client, ("deus_cards_claim", []))
    gold_after = gold(player["id"])
    packet(client, ("deus_cards_claim", []), ("deus_cards_generate", [0, 0]), ("deus_cards_claim", []))
    assert gold(player["id"]) == gold_after


def test_a_card_prize_cannot_be_claimed_without_a_draw(client, player):
    before = gold(player["id"])
    packet(client, ("deus_cards_claim", []))
    assert gold(player["id"]) == before


# --- gold and food produced by the map ---------------------------------------------


def test_habitat_gold_is_bounded_by_what_the_dragons_produced(client, player):
    add_item(player["id"], 810, HABITAT, {"lat": int(time.time())})
    before = gold(player["id"])
    packet(client, ("collect", [810, 10 ** 9]))
    assert gold(player["id"]) - before <= 100        # an empty habitat produces (almost) nothing


def test_only_habitats_pay_gold(client, player):
    add_item(player["id"], 811, FARM)
    before = gold(player["id"])
    packet(client, ("collect", [811, 5000]))
    assert gold(player["id"]) == before


def test_a_crop_cannot_be_harvested_before_it_grows(client, player):
    give(player["id"], gold=10 ** 6, completed_tutorial="1")
    add_item(player["id"], 820, FARM)
    packet(client, ("activate", [820, 5]))                       # a slow crop
    food = info(player["id"])["food"]
    packet(client, ("collect", [820, "fc"]))
    assert info(player["id"])["food"] == food
    assert load_save(player["id"])["map"]["items"]["820"][6].get("cp") == 5

    give(player["id"], cash=1000)
    packet(client, ("speed_collect", [820, 1]), ("collect", [820, "fc"]))
    assert info(player["id"])["food"] > food


def test_the_tutorial_may_harvest_one_crop_right_away(client, player):
    give(player["id"], gold=10 ** 6)                                   # tutorial not completed yet
    add_item(player["id"], 822, FARM)
    food = info(player["id"])["food"]
    packet(client, ("activate", [822, 1]), ("collect", [822, "fc"]))
    assert info(player["id"])["food"] > food                           # the tutorial replay works
    food = info(player["id"])["food"]
    packet(client, ("activate", [822, 1]), ("collect", [822, "fc"]))
    assert info(player["id"])["food"] == food                          # but only once


def test_farm_activation_needs_the_money(client, player):
    give(player["id"], gold=0)
    add_item(player["id"], 821, FARM)
    packet(client, ("activate", [821, 3]))
    assert "cp" not in load_save(player["id"])["map"]["items"]["821"][6]


# --- storage and duplication ---------------------------------------------------------


def test_dragons_cannot_be_conjured_from_nothing(client, player):
    add_item(player["id"], 830, HABITAT)
    packet(client, ("place_stored_dragon", [9001, "830", "Rex", 1041, 40, 0]),
           ("dragonarium_place_stored", ["Rex", 1041, 40, 0]))
    save = load_save(player["id"])
    assert save["map"]["dragons"] == [] and save["privateState"]["dragonarium"] == [[], [], [], [], []]


def test_a_stored_dragon_keeps_its_stored_level(client, player):
    add_item(player["id"], 830, HABITAT)
    edit_save(player["id"], lambda d: d["map"]["store"]["dragons"].append({"iid": DRAGON, "lvl": 3}))
    packet(client, ("place_stored_dragon", [9001, "830", "Rex", DRAGON, 40, 0]))     # claims level 40
    assert load_save(player["id"])["map"]["dragons"] == []
    packet(client, ("place_stored_dragon", [9001, "830", "Rex", DRAGON, 3, 0]))
    dragon = load_save(player["id"])["map"]["dragons"][0]
    assert dragon["xp"] == 8 and load_save(player["id"])["map"]["store"]["dragons"] == []


def test_ids_chosen_by_the_client_cannot_collide(client, player):
    give(player["id"], gold=10 ** 6)
    packet(client, ("buy_egg", [6000, DRAGON]), ("buy_egg", [6000, DRAGON]))
    assert len(load_save(player["id"])["map"]["eggs"]) == 1


def test_overspending_gems_is_refused(client, player):
    give(player["id"], cash=1)
    packet(client, ("dragonarium_add", [0]), ("kompu_boxes_new_list", []), ("kompu_boxes_open_box", []))
    save = load_save(player["id"])
    assert save["playerInfo"]["cash"] == 1 and save["privateState"]["dragonariumSlot"][0] == 2


def test_expansions_are_paid_for(client, player):
    give(player["id"], gold=0, cash=0)
    packet(client, ("expand_island", [90, 1]))
    assert 90 not in load_save(player["id"])["map"]["expansions"]


def test_training_takes_its_time(client, player):
    from dragon_city import storage
    config = storage.load_base_config()
    dragon_cfg = next(i for i in config["items"] if i["id"] == DRAGON)
    attack = dragon_cfg["trainable_attacks"][0]

    add_item(player["id"], 840, 12)                         # any building works as the school
    edit_save(player["id"], lambda d: d["map"]["dragons"].append(
        {"id": 77, "type": DRAGON, "xp": 0, "habitatId": 0, "name": "T", "ts": 0, "work_id": [], "attack": []}))
    packet(client, ("start_training", [840, 77, attack, 0]), ("finish_training", [840]))
    assert "840" in load_save(player["id"])["map"]["work"]          # still training

    edit_save(player["id"], lambda d: d["map"]["work"]["840"].__setitem__(2, 1))      # started long ago
    packet(client, ("finish_training", [840]))
    save = load_save(player["id"])
    assert "840" not in save["map"]["work"] and save["map"]["dragons"][0]["attack"][0] == attack


def test_speed_training_cannot_be_used_for_free(client, player):
    from dragon_city import storage
    attack = next(i for i in storage.load_base_config()["items"] if i["id"] == DRAGON)["trainable_attacks"][0]
    add_item(player["id"], 841, 12)
    edit_save(player["id"], lambda d: d["map"]["dragons"].append(
        {"id": 78, "type": DRAGON, "xp": 0, "habitatId": 0, "name": "T", "ts": 0, "work_id": [], "attack": []}))
    packet(client, ("start_training", [841, 78, attack, 0]))
    give(player["id"], cash=0)
    packet(client, ("speed_training", [841]))
    assert "841" in load_save(player["id"])["map"]["work"]           # not paid, not finished


# --- neighbours and PvP ---------------------------------------------------------------


def test_assists_are_queued_and_paid_only_for_real_clicks(app, client, player):
    other, other_id = second_player(app)
    packet(client, ("assist_receive", [FARM]))
    assert info(player["id"])["xp"] == 0                    # nothing to collect yet

    packet(other, ("assist_neighbor", [player["id"], "[1,2,3]"]),
           ("assist_neighbor", [other_id, "[1]"]),             # cannot assist yourself
           ("assist_neighbor", [123456789, "[1]"]))            # unknown neighbour
    packet(client, ("ping",))                                  # loading the save merges the assists
    save = load_save(player["id"])
    assert save["map"]["receivedAssists"][f"u{other_id}"] == [1, 2, 3]
    assert save["privateState"]["assistRewardsLeft"] == 3

    packet(client, *[("assist_receive", [FARM]) for _ in range(5)])
    assert info(player["id"])["xp"] == 30                   # three rewards, not five


def test_assists_have_a_size_limit(app, client, player):
    other, _ = second_player(app)
    packet(other, ("assist_neighbor", [player["id"], json.dumps(list(range(1000)))]))
    packet(client, ("ping",))
    assert "assistRewardsLeft" not in load_save(player["id"])["privateState"]


def test_pvp_results_need_a_real_fight(client, player):
    packet(client, ("end_attack_f", ["100000050", 1, 1, ""]))        # never started
    assert info(player["id"]).get("pvpLevel", 1) == 1 and load_save(player["id"])["privateState"]["achievement_points"] == 0

    units = packet(client, ("attack_player", ["100000050"]))[0]["result"]
    assert isinstance(units, list)
    packet(client, ("attack_player", ["424242"]))                    # not an opponent
    packet(client, ("end_attack_f", ["100000050", 1, 1, ""]))          # reported instantly
    assert load_save(player["id"])["privateState"]["achievement_points"] == 0

    def age(d):
        d["privateState"]["attacksSent"][0]["time"] -= 60
    edit_save(player["id"], age)
    packet(client, ("end_attack_f", ["100000050", 1, 1, ""]), ("end_attack_f", ["100000050", 1, 1, ""]))
    assert load_save(player["id"])["privateState"]["achievement_points"] == 35     # paid once


def test_tournaments_need_to_begin_before_they_end(client, player):
    packet(client, ("end_tournament", ["1", "{}"]))
    assert load_save(player["id"])["privateState"]["currentTournament"] == 1

    packet(client, ("begin_tournament", []))
    edit_save(player["id"], lambda d: d["privateState"].__setitem__("beginTournamentTs", int(time.time()) - 60))
    packet(client, ("end_tournament", ["1", "{}"]), ("end_tournament", ["1", "{}"]))
    assert load_save(player["id"])["privateState"]["currentTournament"] == 2     # rewarded once


def test_attack_teams_only_use_your_own_dragons(client, player):
    packet(client, ("set_attack_team", ["pvp", "[1,2,3]"]))
    assert "pvp" not in load_save(player["id"])["privateState"].get("teams", {})
    packet(client, ("set_attack_team", ["pvp", json.dumps(list(range(100)))]))
    assert "pvp" not in load_save(player["id"])["privateState"].get("teams", {})


def test_minigame_rewards_have_a_cooldown_and_a_limit(client, player):
    cash = info(player["id"])["cash"]
    assert client.post("/minigame/reward", json={"gems": 3}).status_code == 200
    assert client.post("/minigame/reward", json={"gems": 3}).status_code == 429
    assert client.post("/minigame/reward", json={"gems": 50}).status_code == 400
    assert info(player["id"])["cash"] == cash + 3


def test_the_market_charges_points_and_one_time_offers(client, player):
    market = client.get("/market_data").get_json()
    offer = market["offers"][1]
    assert client.post("/market/redeem", json={"offer_id": offer["id"]}).status_code == 400    # no points
    edit_save(player["id"], lambda d: d["privateState"].__setitem__("achievement_points", 10 ** 6))
    assert client.post("/market/redeem", json={"offer_id": offer["id"]}).status_code == 200
    assert client.post("/market/redeem", json={"offer_id": offer["id"]}).status_code == 400    # sold
    assert client.post("/market/redeem", json={"offer_id": "1; drop"}).status_code == 400


# --- a normal play session still works ---------------------------------------------------


def test_a_normal_session_still_works(client, player):
    give(player["id"], gold=10 ** 6, cash=100, level=7, xp=10 ** 6)
    pid = player["id"]
    packet(client, ("buy", ["900", HABITAT, 10, 10, 0, 0, 1]), ("buy", ["901", FARM, 12, 12, 0, 0, 1]))
    items = load_save(pid)["map"]["items"]
    assert items["900"][6]["tb"] and "901" in items

    packet(client, ("finish_building", ["900", 0]))
    assert "tb" not in load_save(pid)["map"]["items"]["900"][6]

    packet(client, ("buy_egg", [5001, DRAGON]), ("hatch_egg", [5001, 0, 900, "Fido"]))
    save = load_save(pid)
    assert save["map"]["eggs"] == [] and save["map"]["dragons"][0]["name"] == "Fido"
    assert save["map"]["ownedDragons"][str(DRAGON)] == [1, 0, 0]

    packet(client, ("feed_dragon", [5001]), ("rename_dragon", [5001, "Rex"]), ("move", ["901", 20, 20, 1]),
           ("store_item", ["901"]), ("place_stored_item", ["902", FARM, 4, 4]), ("sell", ["902"]))
    save = load_save(pid)
    assert save["map"]["dragons"][0]["name"] == "Rex" and save["map"]["dragons"][0]["xp"] == 1
    assert "901" not in save["map"]["items"] and "902" not in save["map"]["items"]

    packet(client, ("dragonarium_push", [5001]), ("dragonarium_pull", [0, 0, 0, 900]))
    save = load_save(pid)
    assert len(save["map"]["dragons"]) == 1 and save["map"]["dragons"][0]["habitatId"] == 900

    cave_results = packet(client, ("breed_dragon", ["900", 5001, 5002, 0]))
    assert cave_results[0]["result"] == "ok"            # needs two dragons: rejected, nothing broken
    packet(client, ("level_up", [8]), ("complete_tutorial", [1]), ("sync", ["hash"]))
    assert info(pid)["level"] == 8 and info(pid)["completed_tutorial"] == "1"
