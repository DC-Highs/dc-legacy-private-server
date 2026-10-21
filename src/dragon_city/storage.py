"""Persistence of the game config (read-only file) and player state (MongoDB)."""
import copy
import json
import logging
import threading
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any, Dict, Iterator, List, Optional

from dragon_city.config import get_settings
from dragon_city.db.mongo import PENDING_ASSISTS, PLAYERS, get_db

logger = logging.getLogger(__name__)

GAME_CONFIG_FILE = "get_game_config.json"
PLAYER_TEMPLATE_FILE = "get_player_info.json"

MAX_RECEIVED_ASSISTS = 200
MAX_PLAYER_NAME_LENGTH = 24

_base_config: Optional[Dict[str, Any]] = None
_player_template: Optional[Dict[str, Any]] = None


# --- game config -------------------------------------------------------------


def _read_json_file(file_name: str) -> Dict[str, Any]:
    text = (get_settings().seed_dir / file_name).read_text(encoding="utf-8")
    # The captured config ships as "<signature>;<json>".
    if not text.lstrip().startswith(("{", "[")) and ";" in text:
        text = text.split(";", 1)[1]
    return json.loads(text)


def load_base_config() -> Dict[str, Any]:
    """The shared game config. Treat it as read-only: it is cached for the whole process."""
    global _base_config
    if _base_config is None:
        _base_config = _read_json_file(GAME_CONFIG_FILE)
    return _base_config


def config_for_player(player_id: int) -> Dict[str, Any]:
    """The game config as seen by one player (shared config + their own kompu offers)."""
    config = dict(load_base_config())
    doc = get_db()[PLAYERS].find_one({"_id": player_id}, {"kompu_offers": 1})
    if doc and doc.get("kompu_offers") is not None:
        config["kompu_offers"] = doc["kompu_offers"]
    return config


def save_kompu_offers(player_id: int, offers: List[Any]) -> None:
    get_db()[PLAYERS].update_one({"_id": player_id}, {"$set": {"kompu_offers": offers}})


# --- player state ------------------------------------------------------------

_locks_guard = threading.Lock()
_locks: Dict[int, List[Any]] = {}


@contextmanager
def player_lock(player_id: int) -> Iterator[None]:
    """Serialize read-modify-write cycles on one player (the server runs a single process)."""
    with _locks_guard:
        entry = _locks.setdefault(player_id, [threading.RLock(), 0])
        entry[1] += 1
    try:
        with entry[0]:
            yield
    finally:
        with _locks_guard:
            entry[1] -= 1
            if entry[1] == 0:
                _locks.pop(player_id, None)


def _player_template_data() -> Dict[str, Any]:
    global _player_template
    if _player_template is None:
        _player_template = _read_json_file(PLAYER_TEMPLATE_FILE)
    return copy.deepcopy(_player_template)


def normalize_player(data: Dict[str, Any]) -> Dict[str, Any]:
    """Fix the shapes the captured template gets wrong (PHP turns empty maps into lists)."""
    game_map = data.setdefault("map", {})
    store = game_map.get("store")
    if not isinstance(store, dict):
        store = {}
    if not isinstance(store.get("items"), dict):
        store["items"] = {}
    if not isinstance(store.get("dragons"), list):
        store["dragons"] = []
    game_map["store"] = store

    for key, empty in (("eggs", list), ("dragons", list), ("ownedDragons", dict), ("work", dict)):
        if not isinstance(game_map.get(key), empty):
            game_map[key] = empty()

    private_state = data.setdefault("privateState", {})
    if not isinstance(private_state.get("kompuBoxesOpened"), int):
        private_state["kompuBoxesOpened"] = 0
    if not isinstance(private_state.get("achievement_points"), int):
        private_state["achievement_points"] = 0
    return data


def default_player_name(email: str) -> str:
    local = email.split("@", 1)[0]
    cleaned = "".join(ch for ch in local if ch.isalnum() or ch in "._-")[:MAX_PLAYER_NAME_LENGTH]
    return cleaned or "Dragonmaster"


def build_player(player_id: int, name: str) -> Dict[str, Any]:
    data = normalize_player(_player_template_data())
    data["playerInfo"]["name"] = name
    data["playerInfo"]["pid"] = str(player_id)
    data["timestamp"] = int(time.time())
    return data


def _now() -> datetime:
    return datetime.now(timezone.utc)


def create_player(player_id: int, name: str, replace: bool = False) -> Dict[str, Any]:
    """Create the player's save from the template. With ``replace`` an existing save is reset."""
    data = build_player(player_id, name)
    now = _now()
    players = get_db()[PLAYERS]
    if replace:
        players.update_one(
            {"_id": player_id},
            {"$set": {"data": data, "kompu_offers": None, "market": None, "updated_at": now},
             "$setOnInsert": {"created_at": now}},
            upsert=True,
        )
    else:
        players.update_one(
            {"_id": player_id},
            {"$setOnInsert": {"data": data, "kompu_offers": None, "market": None,
                              "created_at": now, "updated_at": now}},
            upsert=True,
        )
    return data


def player_exists(player_id: int) -> bool:
    return get_db()[PLAYERS].count_documents({"_id": player_id}, limit=1) > 0


def delete_player(player_id: int) -> None:
    get_db()[PLAYERS].delete_one({"_id": player_id})
    get_db()[PENDING_ASSISTS].delete_many({"target": player_id})


def peek_player(player_id: int) -> Optional[Dict[str, Any]]:
    """Read a player's save without changing anything (used when visiting a neighbour)."""
    doc = get_db()[PLAYERS].find_one({"_id": player_id}, {"data": 1})
    if not doc:
        return None
    data = normalize_player(doc["data"])
    data["timestamp"] = int(time.time())
    return data


def load_player(player_id: int) -> Optional[Dict[str, Any]]:
    """Load the save of the acting player, merging assists neighbours sent while they were away."""
    data = peek_player(player_id)
    if data is None:
        return None
    _merge_pending_assists(player_id, data)
    return data


def _merge_pending_assists(player_id: int, data: Dict[str, Any]) -> None:
    pending = get_db()[PENDING_ASSISTS]
    docs = list(pending.find({"target": player_id}).limit(100))
    if not docs:
        return

    received = data["map"].get("receivedAssists")
    if not isinstance(received, dict):
        received = {}
        data["map"]["receivedAssists"] = received
    private_state = data["privateState"]

    for doc in docs:
        key = "u" + str(doc["helper"])
        entries = received.setdefault(key, [])
        entries.extend(doc["clicks"])
        del entries[:-MAX_RECEIVED_ASSISTS]
        private_state["assistRewardsLeft"] = private_state.get("assistRewardsLeft", 0) + len(doc["clicks"])
    pending.delete_many({"_id": {"$in": [d["_id"] for d in docs]}})


def save_player(state: Dict[str, Any], player_id: int) -> None:
    get_db()[PLAYERS].update_one({"_id": player_id}, {"$set": {"data": state, "updated_at": _now()}})


def add_pending_assist(target_id: int, helper_id: int, clicks: List[Any]) -> None:
    get_db()[PENDING_ASSISTS].insert_one({"target": target_id, "helper": helper_id, "clicks": clicks, "at": _now()})


def get_market(player_id: int) -> Optional[Dict[str, Any]]:
    doc = get_db()[PLAYERS].find_one({"_id": player_id}, {"market": 1})
    return doc.get("market") if doc else None


def save_market(player_id: int, market: Dict[str, Any]) -> None:
    get_db()[PLAYERS].update_one({"_id": player_id}, {"$set": {"market": market}})


def get_last_minigame_ts(player_id: int) -> int:
    doc = get_db()[PLAYERS].find_one({"_id": player_id}, {"minigame_ts": 1})
    return int(doc.get("minigame_ts", 0)) if doc else 0


def set_last_minigame_ts(player_id: int, timestamp: int) -> None:
    get_db()[PLAYERS].update_one({"_id": player_id}, {"$set": {"minigame_ts": timestamp}})


def player_summary(data: Dict[str, Any]) -> Dict[str, Any]:
    info = data.get("playerInfo", {})
    return {
        "name": info.get("name", ""),
        "level": info.get("level", 1),
        "gold": info.get("gold", 0),
        "cash": info.get("cash", 0),
        "food": info.get("food", 0),
        "xp": info.get("xp", 0),
        "dragons": len(data.get("map", {}).get("dragons", [])),
    }


def players_summaries(player_ids: List[int]) -> Dict[int, Dict[str, Any]]:
    docs = get_db()[PLAYERS].find({"_id": {"$in": player_ids}}, {"data.playerInfo": 1, "data.map.dragons": 1})
    return {d["_id"]: player_summary(d["data"]) for d in docs}
