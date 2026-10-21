"""Command registry and the context handlers run with."""
import importlib
import pkgutil
import time
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional

from dragon_city.enums import Command

RESULT_OK = "ok"


@dataclass
class CommandContext:
    """Everything a command handler needs to apply one client command.

    Handlers mutate ``player_data`` in place and may set ``result`` to the value
    returned to the client for this command (defaults to ``"ok"``).
    """

    user_id: str
    cmd: str
    number: Any
    args: List[Any]
    player_data: Dict[str, Any]
    game_config: Dict[str, Any]
    items_index: Dict[str, Dict[str, Any]]
    result: Any = RESULT_OK

    @property
    def info(self) -> Dict[str, Any]:
        """The player's ``playerInfo`` (gold, cash, food, xp, level...)."""
        return self.player_data["playerInfo"]

    @property
    def private_state(self) -> Dict[str, Any]:
        return self.player_data["privateState"]

    @property
    def map(self) -> Dict[str, Any]:
        return self.player_data["map"]

    @property
    def server_ts(self) -> int:
        """Timestamp of the current request, as stamped by ``load_player``."""
        return self.player_data.get("timestamp", int(time.time()))


Handler = Callable[[CommandContext], None]

_handlers: Dict[Command, Handler] = {}
_loaded = False


def command(*commands: Command) -> Callable[[Handler], Handler]:
    """Register the decorated function as the handler of ``commands``."""

    def decorator(func: Handler) -> Handler:
        for cmd in commands:
            if cmd in _handlers:
                raise ValueError(f"Command {cmd.value} already has a handler")
            _handlers[cmd] = func
        return func

    return decorator


def get_handler(cmd: Any) -> Optional[Handler]:
    """Return the handler for a raw command name, or ``None`` if it is not implemented."""
    try:
        return _handlers.get(Command(cmd))
    except ValueError:
        return None


def load_commands() -> None:
    """Import every command module so their ``@command`` decorators run."""
    global _loaded
    if _loaded:
        return

    package = importlib.import_module("dragon_city.commands")
    for module in pkgutil.iter_modules(package.__path__):
        importlib.import_module(f"{package.__name__}.{module.name}")
    _loaded = True


def implemented_commands() -> List[Command]:
    return sorted(_handlers, key=lambda c: c.value)
