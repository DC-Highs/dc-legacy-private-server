"""In-memory state shared between requests."""
import queue
from typing import Dict

from dragon_city.enums import SseEvent

_channels: Dict[str, "queue.Queue[str]"] = {}


def get_channel(user_id: str) -> "queue.Queue[str]":
    """Return the SSE queue of ``user_id``, creating it on first use."""
    if user_id not in _channels:
        _channels[user_id] = queue.Queue()
    return _channels[user_id]


def notify(user_id: str, event: SseEvent) -> None:
    """Push ``event`` to ``user_id`` if that player has an open channel."""
    if user_id in _channels:
        _channels[user_id].put(event.value)
