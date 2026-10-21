"""Command line: ``python -m src <serve|migrate|create-admin|seed>``."""
import argparse
import logging
import sys
import time
from pathlib import Path
from typing import List, Optional

from alembic import command as alembic_command
from alembic.config import Config
from sqlalchemy import text
from sqlalchemy.exc import OperationalError

from src.config import get_settings
from src.logging_config import configure_logging

logger = logging.getLogger("src")

MIGRATIONS_DIR = Path(__file__).resolve().parent / "migrations"
DB_WAIT_SECONDS = 60


def _alembic_config() -> Config:
    config = Config()
    config.set_main_option("script_location", str(MIGRATIONS_DIR))
    config.set_main_option("sqlalchemy.url", get_settings().database_url.replace("%", "%%"))
    return config


def wait_for_database(timeout: int = DB_WAIT_SECONDS) -> None:
    from src.db.postgres import get_engine

    deadline = time.monotonic() + timeout
    while True:
        try:
            with get_engine().connect() as connection:
                connection.execute(text("SELECT 1"))
            return
        except OperationalError:
            if time.monotonic() > deadline:
                raise
            logger.info("Waiting for PostgreSQL...")
            time.sleep(2)


def migrate() -> None:
    wait_for_database()
    alembic_command.upgrade(_alembic_config(), "head")
    logger.info("Database schema is up to date")


def create_admin(email: str, password: str) -> None:
    from src.app import startup_tasks  # noqa: F401  (imports register all models)
    from src.auth import service
    from src.db.mongo import ensure_indexes
    from src.db.postgres import session_scope

    ensure_indexes()
    with session_scope() as session:
        user = service.ensure_admin(session, email, password)
    logger.info("Administrator account ready: %s (id %s)", user.email, user.id)


def seed() -> None:
    from src.db.mongo import ensure_indexes
    from src.game.pvp import seed_pvp_data

    ensure_indexes()
    seed_pvp_data()


def serve() -> None:
    """Development server. In production use gunicorn (see the Dockerfile)."""
    from src.app import create_app

    app = create_app()
    app.run(host="127.0.0.1", port=8080, debug=False, threaded=True)


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(prog="dragon-city")
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("serve", help="run the development server (default)")
    sub.add_parser("migrate", help="apply the PostgreSQL migrations")
    sub.add_parser("seed", help="load the bundled PvP opponents into MongoDB")
    admin = sub.add_parser("create-admin", help="create an administrator account")
    admin.add_argument("--email", required=True)
    admin.add_argument("--password", required=True)

    args = parser.parse_args(argv)
    configure_logging(get_settings().log_level)

    if args.command == "migrate":
        migrate()
    elif args.command == "seed":
        seed()
    elif args.command == "create-admin":
        create_admin(args.email, args.password)
    else:
        serve()
    return 0


if __name__ == "__main__":
    sys.exit(main())
