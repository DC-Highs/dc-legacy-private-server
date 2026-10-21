"""WSGI entry point for gunicorn: ``gunicorn dragon_city.wsgi:app``."""
from dragon_city.app import create_app
from dragon_city.config import get_settings
from dragon_city.logging_config import configure_logging

configure_logging(get_settings().log_level)
app = create_app()
