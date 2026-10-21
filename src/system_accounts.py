"""Accounts that belong to the game itself, not to a person."""
import logging
import secrets

from sqlalchemy.orm import Session

from src import storage
from src.auth.passwords import hash_password
from src.config import DEUS_PLAYER_ID
from src.db.models import User

logger = logging.getLogger(__name__)

DEUS_NAME = "Deus"
DEUS_EMAIL = "deus@system.dragoncity.invalid"


def ensure_deus(session: Session) -> User:
    """Create Deus, the Dragon Master, if he is missing: an account nobody can log into and a save.

    The Flash client has a "Deus" card in the neighbours bar that visits this fixed player id.
    Without a save behind it, visiting Deus left the game on a loading bar forever.
    """
    user = session.get(User, DEUS_PLAYER_ID)
    if user is None:
        user = User(
            id=DEUS_PLAYER_ID,
            email=DEUS_EMAIL,
            password_hash=hash_password(secrets.token_urlsafe(48)),  # nobody knows it
            is_admin=False,
            is_active=False,
        )
        session.add(user)
        session.flush()
        logger.info("Created the system account of Deus (id %s)", DEUS_PLAYER_ID)

    if not storage.player_exists(DEUS_PLAYER_ID):
        storage.create_player(DEUS_PLAYER_ID, DEUS_NAME)
        logger.info("Created the save of Deus")
    return user
