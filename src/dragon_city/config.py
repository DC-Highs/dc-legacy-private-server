"""Settings (read from environment variables) and constants shared across the server."""
import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Mapping, Optional, Tuple

from sqlalchemy.engine import URL

# src/dragon_city/config.py -> repository root
BASE_DIR = Path(__file__).resolve().parents[2]

# HMAC key the Flash client uses to verify signed packets. It ships inside the SWF,
# so it is not a secret; it only has to match what the client expects.
SECRET_KEY = "RGhXbiy4xEeDnSNX1oBG"

PVP_PAGE_SIZE = 8
SSE_KEEPALIVE_SECONDS = 20

# 1x1 transparent GIF returned for the analytics stubs.
PIXEL_GIF = (
    b"GIF89a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xff\xff\xff!\xf9\x04\x01\x00\x00\x00\x00"
    b",\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;"
)

# Hosts the Flash client has hardcoded; the web client rewrites them to this server.
LEGACY_GAME_HOSTS = (
    "static.socialpointgames.com",
    "sp-translations.socialpointgames.com",
    "api.omniata.com",
    "graph.facebook.com",
    "ajax.googleapis.com",
    "www.google-analytics.com",
    "ssl.google-analytics.com",
    "google-analytics.com",
)


def _flag(value: Optional[str], default: bool) -> bool:
    if value is None or value == "":
        return default
    return value.strip().lower() in ("1", "true", "yes", "on")


def _path(env: Mapping[str, str], name: str, default: Path) -> Path:
    return Path(env[name]) if env.get(name) else default


def _database_url(env: Mapping[str, str]) -> str:
    """``DATABASE_URL``, or one assembled from POSTGRES_* parts (passwords are escaped for us)."""
    if env.get("DATABASE_URL"):
        return env["DATABASE_URL"]
    return URL.create(
        "postgresql+psycopg",
        username=env.get("POSTGRES_USER", "dragon"),
        password=env.get("POSTGRES_PASSWORD", "dragon"),
        host=env.get("POSTGRES_HOST", "localhost"),
        port=int(env.get("POSTGRES_PORT", "5432")),
        database=env.get("POSTGRES_DB", "dragoncity"),
    ).render_as_string(hide_password=False)


@dataclass(frozen=True)
class Settings:
    database_url: str
    mongo_url: str
    mongo_db: str
    mongo_user: str
    mongo_password: str
    cookie_secure: bool
    session_days: int
    registration_enabled: bool
    allowed_origins: Tuple[str, ...]
    trust_proxy: bool
    admin_email: str
    admin_password: str
    swf_version: str
    log_level: str
    seed_dir: Path
    flash_dir: Path
    assets_dir: Path
    domain_map_dir: Path
    frontend_dist: Path

    @classmethod
    def from_env(cls, env: Optional[Mapping[str, str]] = None) -> "Settings":
        env = os.environ if env is None else env
        origins = tuple(o.strip().rstrip("/") for o in env.get("ALLOWED_ORIGINS", "").split(",") if o.strip())
        return cls(
            database_url=_database_url(env),
            mongo_url=env.get("MONGO_URL", "mongodb://localhost:27017"),
            mongo_db=env.get("MONGO_DB", "dragoncity"),
            mongo_user=env.get("MONGO_USER", ""),
            mongo_password=env.get("MONGO_PASSWORD", ""),
            cookie_secure=_flag(env.get("COOKIE_SECURE"), False),
            session_days=int(env.get("SESSION_DAYS", "14")),
            registration_enabled=_flag(env.get("REGISTRATION_ENABLED"), True),
            allowed_origins=origins,
            trust_proxy=_flag(env.get("TRUST_PROXY"), False),
            admin_email=env.get("ADMIN_EMAIL", ""),
            admin_password=env.get("ADMIN_PASSWORD", ""),
            swf_version=env.get("GAME_SWF", "Base_sec_0.6.7c.swf"),
            log_level=env.get("LOG_LEVEL", env.get("DRAGON_CITY_LOG_LEVEL", "INFO")),
            seed_dir=_path(env, "SEED_DIR", BASE_DIR / "web" / "srv"),
            flash_dir=_path(env, "FLASH_DIR", BASE_DIR / "flash"),
            assets_dir=_path(env, "ASSETS_DIR", BASE_DIR / "assets"),
            domain_map_dir=_path(env, "DOMAIN_MAP_DIR", BASE_DIR / "domains"),
            frontend_dist=_path(env, "FRONTEND_DIST", BASE_DIR / "frontend" / "dist"),
        )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings.from_env()
