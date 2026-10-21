"""PvP opponents (stored in MongoDB) and their generation."""
import json
import logging
import random
from typing import Any, Dict, List, Optional

from dragon_city.config import PVP_PAGE_SIZE, get_settings
from dragon_city.db.mongo import PVP_ISLE, PVP_PLAYERS, get_db
from dragon_city.enums import GroupType
from dragon_city.names import DRAGON_NAMES, FIRST_NAMES, LAST_NAMES
from dragon_city.storage import load_base_config

logger = logging.getLogger(__name__)

PVP_ISLE_FILE = "get_pvp_isle.json"
PVP_PLAYERS_FILE = "pvp_players_info.json"
OPPONENTS_PER_BATCH = 8
OPPONENT_PICTURE = "http://graph.facebook.com/1000000000000/picture?type=square"


def seed_pvp_data() -> None:
    """Import the bundled opponents the first time the database is empty."""
    db = get_db()
    if db[PVP_ISLE].count_documents({}, limit=1):
        return

    seed_dir = get_settings().seed_dir
    isle_path, players_path = seed_dir / PVP_ISLE_FILE, seed_dir / PVP_PLAYERS_FILE
    if not isle_path.exists() or not players_path.exists():
        logger.warning("PvP seed files not found in %s, the PvP isle will be empty", seed_dir)
        return

    isle = json.loads(isle_path.read_text(encoding="utf-8"))
    players = json.loads(players_path.read_text(encoding="utf-8"))

    if isle:
        db[PVP_ISLE].insert_many({"_id": str(e["id"]), "order": i, "entry": e} for i, e in enumerate(isle))
    if players:
        db[PVP_PLAYERS].insert_many({"_id": str(pid), "data": data} for pid, data in players.items())
    logger.info("Seeded %s PvP opponents", len(isle))


def pvp_page(level: int) -> List[Dict[str, Any]]:
    start = max(0, (level - 1) * PVP_PAGE_SIZE)
    docs = get_db()[PVP_ISLE].find().sort("order", 1).skip(start).limit(PVP_PAGE_SIZE)
    return [d["entry"] for d in docs]


def get_pvp_player(opponent_id: str) -> Optional[Dict[str, Any]]:
    doc = get_db()[PVP_PLAYERS].find_one({"_id": str(opponent_id)})
    return doc["data"] if doc else None


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
    """Append a batch of random opponents and return the new total."""
    db = get_db()
    dragon_pool = build_dragon_pool(load_base_config())

    entries = [d["entry"] for d in db[PVP_ISLE].find({}, {"entry.id": 1, "entry.islandNumber": 1, "order": 1})]
    last_id = max((int(e["id"]) for e in entries), default=100000000)
    last_island = max((e.get("islandNumber", 1) for e in entries), default=1)
    next_order = db[PVP_ISLE].count_documents({})

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

        entry = {
            "id": new_id, "name": name, "level": lvl,
            "pvplevel": pvp_lvl, "pvpIsle": pvp_isle_val,
            "islandNumber": last_island + (i % 2),
            "pic": OPPONENT_PICTURE,
        }

        team_size = roll_team_size()
        dragons = []
        team_pvp = []
        for d_idx in range(1, team_size + 1):
            dragons.append({
                "id": d_idx, "type": get_dragon_type_for_level(lvl, dragon_pool),
                "xp": random.randint(16, 156),
                "habitatId": 0,
                "name": random.choice(DRAGON_NAMES),
                "ts": 0, "work_id": [], "attack": [],
            })
            team_pvp.append({"id": d_idx})

        db[PVP_ISLE].insert_one({"_id": new_id, "order": next_order + i - 1, "entry": entry})
        db[PVP_PLAYERS].insert_one({
            "_id": new_id,
            "data": {"map": {"dragons": dragons}, "privateState": {"teams": {"pvp": team_pvp}}},
        })
        logger.info("Generated PvP opponent %s (id=%s, level=%s, dragons=%s)", name, new_id, lvl, team_size)

    total = db[PVP_ISLE].count_documents({})
    logger.info("PvP data updated, total opponents: %s", total)
    return total
