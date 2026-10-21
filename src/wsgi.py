"""WSGI entry point for gunicorn: ``gunicorn src.wsgi:app``."""
from src.app import create_app
from src.config import get_settings
from src.logging_config import configure_logging

configure_logging(get_settings().log_level)
app = create_app()
