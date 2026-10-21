"""Command registry and the context handlers run with."""
import importlib
import pkgutil
import time
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional

from dragon_city.commands.validation import (
    MAX_NAME_LENGTH,
    MAX_SAFE_INT,
    reject,
    to_flag,
    to_int,
    to_iso_id,
    to_text,
    to_uid,
)
from dragon_city.enums import Command, Resource
from dragon_city.game.items import get_item_config

RESULT_OK = "ok"


@dataclass
class CommandContext:
    """Everything a command handler needs to apply one client command.

    Handlers mutate ``player_data`` in place and may set ``result`` to the value
    returned to the client for this command (defaults to ``"ok"``). Arguments are
    untrusted: read them through the ``*_arg`` helpers, which reject bad input.
    """

    user_id: int
    cmd: str
    number: Any
    args: List[Any]
    player_data: Dict[str, Any]
    game_config: Dict[str, Any]
    items_index: Dict[str, Dict[str, Any]]
    result: Any = RESULT_OK

    # --- state shortcuts -------------------------------------------------------

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
        """Timestamp of the current request, as stamped when the save was loaded."""
        return self.player_data.get("timestamp", int(time.time()))

    # --- argument helpers ------------------------------------------------------

    def arg(self, index: int, name: str = "argument") -> Any:
        if index >= len(self.args):
            reject(f"missing {name} (argument {index})")
        return self.args[index]

    def int_arg(self, index: int, name: str, minimum: int = -MAX_SAFE_INT, maximum: int = MAX_SAFE_INT) -> int:
        return to_int(self.arg(index, name), name, minimum, maximum)

    def uid_arg(self, index: int, name: str) -> int:
        return to_uid(self.arg(index, name), name)

    def flag_arg(self, index: int, name: str) -> int:
        return to_flag(self.arg(index, name), name)

    def iso_arg(self, index: int, name: str = "iso id") -> str:
        return to_iso_id(self.arg(index, name), name)

    def text_arg(self, index: int, name: str, max_length: int = MAX_NAME_LENGTH, allow_empty: bool = False) -> str:
        return to_text(self.arg(index, name), name, max_length, allow_empty)

    # --- lookups that reject unknown things ------------------------------------

    def item_config(self, item_id: Any) -> Dict[str, Any]:
        item_cfg = get_item_config(self.game_config, item_id)
        if item_cfg is None:
            reject(f"item {item_id} does not exist in the game config")
        return item_cfg

    def map_item(self, iso_id: str) -> list:
        item = self.map["items"].get(iso_id)
        if item is None:
            reject(f"object {iso_id} is not on the map")
        return item

    def find_dragon(self, dragon_uid: int) -> Dict[str, Any]:
        for dragon in self.map["dragons"]:
            if str(dragon.get("id")) == str(dragon_uid):
                return dragon
        reject(f"dragon {dragon_uid} is not on the map")

    def find_egg(self, egg_uid: int) -> Dict[str, Any]:
        for egg in self.map["eggs"]:
            if str(egg.get("id")) == str(egg_uid):
                return egg
        reject(f"egg {egg_uid} is not in the hatchery")

    def new_uid(self, index: int, name: str) -> int:
        """A client-generated id for a new egg or dragon; it must not be in use."""
        uid = self.uid_arg(index, name)
        used = {e.get("id") for e in self.map["eggs"]} | {d.get("id") for d in self.map["dragons"]}
        for tab in self.private_state.get("dragonarium", []):
            used.update(d.get("id") for d in tab)
        if uid in used:
            reject(f"{name} {uid} is already in use")
        return uid

    # --- money -----------------------------------------------------------------

    def pay(self, gold: int = 0, cash: int = 0, food: int = 0) -> None:
        """Charge resources, rejecting the command when the player cannot afford it."""
        costs = ((Resource.GOLD, gold), (Resource.CASH, cash), (Resource.FOOD, food))
        for resource, amount in costs:
            if amount < 0:
                reject("negative cost")
            if self.info[resource] < amount:
                reject(f"not enough {resource.value}: needs {amount}, has {self.info[resource]}")
        for resource, amount in costs:
            if amount:
                self.info[resource] -= amount


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
