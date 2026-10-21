"""MongoDB access (game state, PvP opponents, pending assists)."""
import logging
from typing import Any, Optional

from pymongo import ASCENDING, MongoClient
from pymongo.database import Database

from src.config import get_settings

logger = logging.getLogger(__name__)

_client: Optional[Any] = None
_database: Optional[Database] = None

PLAYERS = "players"
PVP_ISLE = "pvp_isle"
PVP_PLAYERS = "pvp_players"
PENDING_ASSISTS = "pending_assists"


def init_mongo(client: Optional[Any] = None, db_name: Optional[str] = None) -> Database:
    """Create (or replace) the global client; tests inject a ``mongomock`` client."""
    global _client, _database
    settings = get_settings()
    if client is None:
        credentials = {}
        if settings.mongo_user:
            credentials = {"username": settings.mongo_user, "password": settings.mongo_password, "authSource": "admin"}
        client = MongoClient(settings.mongo_url, tz_aware=True, serverSelectionTimeoutMS=5000, **credentials)
    _client = client
    _database = _client[db_name or settings.mongo_db]
    return _database


def get_db() -> Database:
    return _database if _database is not None else init_mongo()


def ensure_indexes() -> None:
    db = get_db()
    db[PVP_ISLE].create_index([("order", ASCENDING)])
    db[PENDING_ASSISTS].create_index([("target", ASCENDING)])
    logger.info("MongoDB indexes ensured")
