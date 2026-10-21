"""SQLAlchemy engine and session management."""
from contextlib import contextmanager
from typing import Iterator, Optional

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from src.config import get_settings

_engine: Optional[Engine] = None
_session_factory: Optional[sessionmaker] = None


def init_engine(url: Optional[str] = None, **kwargs) -> Engine:
    """Create (or replace) the global engine; ``url`` defaults to ``DATABASE_URL``."""
    global _engine, _session_factory
    if _engine is not None:
        _engine.dispose()
    _engine = create_engine(url or get_settings().database_url, pool_pre_ping=True, **kwargs)
    _session_factory = sessionmaker(bind=_engine, expire_on_commit=False)
    return _engine


def get_engine() -> Engine:
    return _engine if _engine is not None else init_engine()


@contextmanager
def session_scope() -> Iterator[Session]:
    """A transactional session: commits on success, rolls back on error."""
    get_engine()
    assert _session_factory is not None
    session = _session_factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
