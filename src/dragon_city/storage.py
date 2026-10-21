"""Persistence of game config, player saves and PvP data (JSON files under web/srv)."""
import json
import logging
import shutil
import time
from pathlib import Path
from typing import Any, Dict, Optional

from dragon_city.config import SRV_DIR

logger = logging.getLogger(__name__)

GAME_CONFIG_FILE = "get_game_config.json"
PVP_ISLE_FILE = "get_pvp_isle.json"
PVP_PLAYERS_FILE = "pvp_players_info.json"
PLAYER_TEMPLATE_FILE = "get_player_info.json"

_USER_COPIED_FILES = (GAME_CONFIG_FILE, PVP_ISLE_FILE, PVP_PLAYERS_FILE)

_game_config_cache: Dict[Path, Dict[str, Any]] = {}


def user_dir(user_id: Any) -> Path:
    return SRV_DIR / str(user_id)


def _user_or_default_path(user_id: Optional[Any], file_name: str) -> Path:
    default_path = SRV_DIR / file_name
    if user_id:
        user_path = user_dir(user_id) / file_name
        return user_path if user_path.exists() else default_path
    return default_path


def load_game_config(user_id: Optional[Any] = None) -> Dict[str, Any]:
    """Load the (per-user, falling back to the default) game config, cached by mtime."""
    path = _user_or_default_path(user_id, GAME_CONFIG_FILE)

    cached = _game_config_cache.get(path)
    mtime = path.stat().st_mtime

    if cached and cached["mtime"] == mtime:
        return cached["data"]

    with open(path, "r", encoding="utf-8") as f:
        data = json.loads(f.read())

    _game_config_cache[path] = {"data": data, "mtime": mtime}
    return data


def save_game_config(game_config: Dict[str, Any], user_id: Any) -> None:
    directory = user_dir(user_id)
    directory.mkdir(parents=True, exist_ok=True)
    with open(directory / GAME_CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(game_config, f, separators=(",", ":"))


def load_player(user_id: Any) -> Dict[str, Any]:
    """Load a player save, creating it from the template on first access."""
    directory = user_dir(user_id)
    user_file = directory / f"{user_id}.json"
    template_file = SRV_DIR / PLAYER_TEMPLATE_FILE

    if not user_file.exists():
        directory.mkdir(parents=True, exist_ok=True)
        for file_name in _USER_COPIED_FILES:
            src = SRV_DIR / file_name
            if src.exists():
                shutil.copy2(src, directory / file_name)

        if not template_file.exists():
            logger.critical("Player template is missing in %s", SRV_DIR)
            return {}
        with open(template_file, "r", encoding="utf-8") as f:
            player_data = json.load(f)
    else:
        with open(user_file, "r", encoding="utf-8") as f:
            player_data = json.load(f)

    player_data["timestamp"] = int(time.time())
    return player_data


def save_player(state: Dict[str, Any], user_id: Any) -> None:
    directory = user_dir(user_id)
    directory.mkdir(parents=True, exist_ok=True)
    with open(directory / f"{user_id}.json", "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)


def load_pvp_isle(user_id: Optional[Any] = None) -> Any:
    path = _user_or_default_path(user_id, PVP_ISLE_FILE)

    if not path.exists():
        logger.warning("PvP isle file not found: %s", path)
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.loads(f.read())


def load_pvp_players() -> Dict[str, Any]:
    with open(SRV_DIR / PVP_PLAYERS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)
