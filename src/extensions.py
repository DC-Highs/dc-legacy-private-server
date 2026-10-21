"""Flask extensions shared by the blueprints."""
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# In-memory storage is enough: the server runs a single process (see the README).
limiter = Limiter(key_func=get_remote_address, storage_uri="memory://", default_limits=[])


def player_key() -> str:
    """Rate-limit key: the logged-in account, or the client address when there is none."""
    from src.auth.context import current_user

    user = current_user()
    return f"player:{user.id}" if user is not None else get_remote_address()
