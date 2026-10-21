"""Packet signing."""
import hashlib
import hmac
import json
from typing import Any

from dragon_city.config import SECRET_KEY


def sign_packet(payload: Any) -> str:
    """Serialize ``payload`` and prefix it with its HMAC-SHA256 signature."""
    json_payload = json.dumps(payload, separators=(",", ":"))
    signature = hmac.new(
        SECRET_KEY.encode("utf-8"),
        json_payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return f"{signature};{json_payload}"
