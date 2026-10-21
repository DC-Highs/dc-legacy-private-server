"""PvP opponent generation."""
import json
import logging
import random
from typing import Any, Dict, List

from dragon_city.config import SRV_DIR
from dragon_city.enums import GroupType
from dragon_city.names import DRAGON_NAMES, FIRST_NAMES, LAST_NAMES
from dragon_city.storage import PVP_ISLE_FILE, PVP_PLAYERS_FILE, load_game_config

logger = logging.getLogger(__name__)

OPPONENTS_PER_BATCH = 8
OPPONENT_PICTURE = "http://graph.facebook.com/1000000000000/picture?type=square"


def build_dragon_pool(config_data: Dict[str, Any]) -> Dict[int, List[int]]:
    pool: Dict[int, List[int]] = {1: [], 2: [], 3: [], 4: [], 5: []}
    for item in config_data.get("items", []):
        if item.get("group_type") == GroupType.DRAGON:
            cat = item.get("category", 1)
            d_id = item.get("id")
            if cat in pool:
                pool[cat].append(d_id)
    return pool


def get_dragon_type_for_level(level: int, pool: Dict[int, List[int]]) -> int:
    if level <= 15:
        allowed = [1, 2]
    elif level <= 30:
        allowed = [2, 3, 4]
    else:
        allowed = [3, 4, 5]
    valid_cats = [c for c in allowed if pool[c]] or [1]
    chosen_cat = random.choice(valid_cats)
    return random.choice(pool[chosen_cat])


def roll_team_size() -> int:
    roll = random.random()
    if roll <= 0.85:
        return 3
    elif roll <= 0.95:
        return 2
    else:
        return 1


def generate_pvp_opponents() -> int:
    """Append a batch of random opponents to the PvP files and return the new total."""
    pvp_isle_path = SRV_DIR / PVP_ISLE_FILE
    pvp_players_path = SRV_DIR / PVP_PLAYERS_FILE

    with open(pvp_isle_path, "r", encoding="utf-8") as f:
        pvp_isle = json.load(f)
    with open(pvp_players_path, "r", encoding="utf-8") as f:
        pvp_players = json.load(f)

    config_data = load_game_config()
    dragon_pool = build_dragon_pool(config_data)

    last_id = max(int(p["id"]) for p in pvp_isle)
    last_island = max(p.get("islandNumber", 1) for p in pvp_isle)

    for i in range(1, OPPONENTS_PER_BATCH + 1):
        new_id = str(last_id + i)
        name = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}".strip()
        lvl = random.randint(12, 60)
        pvp_lvl = random.randint(1, max(1, lvl // 4))

        if lvl < 20:
            pvp_isle_val = 0
        elif lvl < 35:
            pvp_isle_val = 1
        elif lvl < 50:
            pvp_isle_val = 2
        else:
            pvp_isle_val = 3

        pvp_isle.append({
            "id": new_id, "name": name, "level": lvl,
            "pvplevel": pvp_lvl, "pvpIsle": pvp_isle_val,
            "islandNumber": last_island + (i % 2),
            "pic": OPPONENT_PICTURE,
        })

        team_size = roll_team_size()
        dragons = []
        team_pvp = []

        for d_idx in range(1, team_size + 1):
            d_type = get_dragon_type_for_level(lvl, dragon_pool)
            dragons.append({
                "id": d_idx, "type": d_type,
                "xp": random.randint(16, 156),
                "habitatId": 0,
                "name": random.choice(DRAGON_NAMES),
                "ts": 0, "work_id": [], "attack": [],
            })
            team_pvp.append({"id": d_idx})

        pvp_players[new_id] = {
            "map": {"dragons": dragons},
            "privateState": {"teams": {"pvp": team_pvp}},
        }

        logger.info("Generated PvP opponent %s (id=%s, level=%s, dragons=%s)", name, new_id, lvl, team_size)

    with open(pvp_isle_path, "w", encoding="utf-8") as f:
        json.dump(pvp_isle, f, indent=2)
    with open(pvp_players_path, "w", encoding="utf-8") as f:
        json.dump(pvp_players, f, indent=2)

    logger.info("PvP data updated, total opponents: %s", len(pvp_isle))
    return len(pvp_isle)
