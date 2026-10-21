"""In-memory state shared between requests."""
import queue
import threading
from typing import Dict

from src.enums import SseEvent

MAX_QUEUED_EVENTS = 50

_channels: Dict[int, "queue.Queue[str]"] = {}
_guard = threading.Lock()


def get_channel(player_id: int) -> "queue.Queue[str]":
    """Return the SSE queue of ``player_id``, creating it on first use."""
    with _guard:
        if player_id not in _channels:
            _channels[player_id] = queue.Queue(maxsize=MAX_QUEUED_EVENTS)
        return _channels[player_id]


def notify(player_id: int, event: SseEvent) -> None:
    """Push ``event`` to ``player_id`` if that player has an open channel."""
    channel = _channels.get(player_id)
    if channel is None:
        return
    try:
        channel.put_nowait(event.value)
    except queue.Full:
        pass
