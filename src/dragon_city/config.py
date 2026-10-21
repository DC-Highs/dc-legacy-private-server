"""Paths and constants shared across the server."""
from pathlib import Path

# src/dragon_city/config.py -> repository root
BASE_DIR = Path(__file__).resolve().parents[2]

TEMPLATES_DIR = BASE_DIR / "templates"
FLASH_DIR = BASE_DIR / "flash"
WEB_DIR = BASE_DIR / "web"
SRV_DIR = WEB_DIR / "srv"
DOMAIN_MAP_DIR = BASE_DIR / "domains"
ASSETS_DIR = BASE_DIR / "assets"

# HMAC key the Flash client uses to verify signed packets.
SECRET_KEY = "RGhXbiy4xEeDnSNX1oBG"

SERVER_HOST = "127.0.0.1"
SERVER_PORT = 80
POLICY_SERVER_PORT = 5840

HOSTS_PATH = Path(r"C:\Windows\System32\drivers\etc\hosts")
HOSTS_MARKER = "# --- Dragon City Flash ---"
HOSTS_ENTRIES = [
    "127.0.0.1 static.socialpointgames.com",
    "127.0.0.1 ajax.googleapis.com",
    "127.0.0.1 api.omniata.com",
    "127.0.0.1 sp-translations.socialpointgames.com",
    "127.0.0.1 graph.facebook.com",
    "127.0.0.1 www.google-analytics.com",
    "127.0.0.1 ssl.google-analytics.com",
    "127.0.0.1 google-analytics.com",
]

PVP_PAGE_SIZE = 8
SSE_KEEPALIVE_SECONDS = 20

# 1x1 transparent GIF returned for the analytics stubs.
PIXEL_GIF = (
    b"GIF89a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xff\xff\xff!\xf9\x04\x01\x00\x00\x00\x00"
    b",\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;"
)
