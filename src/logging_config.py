"""Logging setup for the whole application."""
import logging
import os

LOG_FORMAT = "%(asctime)s %(levelname)-7s %(name)s: %(message)s"
LOG_DATE_FORMAT = "%H:%M:%S"
LOG_LEVEL_ENV = "DRAGON_CITY_LOG_LEVEL"


def configure_logging(level: str = "") -> None:
    """Configure the root logger; ``DRAGON_CITY_LOG_LEVEL`` overrides the default (INFO)."""
    level_name = (level or os.environ.get(LOG_LEVEL_ENV, "INFO")).upper()
    logging.basicConfig(
        level=getattr(logging, level_name, logging.INFO),
        format=LOG_FORMAT,
        datefmt=LOG_DATE_FORMAT,
    )
