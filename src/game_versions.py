"""The game client versions (SWF files) in flash/versions, and which one is served."""
import re
from typing import Dict, List

from sqlalchemy.orm import Session

from src.config import get_settings
from src.db.models import AppSetting

SETTING_KEY = "game_swf"
# Folder of the Flash dir that holds the clients; the loader (DCLoader.swf) stays next to it.
VERSIONS_SUBDIR = "versions"
# Only plain file names: no spaces or separators, so a name can be put in a URL as it is.
_VERSION_FILE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*\.swf$")
_LABEL = re.compile(r"^Base_sec_(.+)\.swf$")


def _natural_key(name: str):
    return [int(part) if part.isdigit() else part for part in re.split(r"(\d+)", name)]


def _label(file: str) -> str:
    match = _LABEL.match(file)
    return match.group(1) if match else file[: -len(".swf")]


def available_versions() -> List[Dict[str, str]]:
    """The versions found on disk, oldest first: ``[{"file": ..., "version": ...}]``."""
    directory = get_settings().flash_dir / VERSIONS_SUBDIR
    if not directory.is_dir():
        return []
    files = [
        entry.name
        for entry in directory.iterdir()
        if entry.is_file() and _VERSION_FILE.match(entry.name)
    ]
    return [{"file": name, "version": _label(name)} for name in sorted(files, key=_natural_key)]


def default_version() -> str:
    """The version used until an admin picks one (``GAME_SWF``)."""
    return get_settings().swf_version


def selected_version(session: Session) -> str:
    """The version to serve: the admin's choice if that file still exists, else the default."""
    stored = session.get(AppSetting, SETTING_KEY)
    if stored is not None and any(v["file"] == stored.value for v in available_versions()):
        return stored.value
    return default_version()


def select_version(session: Session, file: str) -> bool:
    """Remember ``file`` as the served version; ``False`` when it is not an available version."""
    if not any(v["file"] == file for v in available_versions()):
        return False
    stored = session.get(AppSetting, SETTING_KEY)
    if stored is None:
        session.add(AppSetting(key=SETTING_KEY, value=file))
    else:
        stored.value = file
    return True
