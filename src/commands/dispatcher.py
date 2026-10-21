"""Runs the commands of a ``packet.php`` request against a player save."""
import copy
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List

from src.commands.base import RESULT_OK, CommandContext, get_handler, load_commands
from src.commands.validation import CommandRejected, check_json_depth
from src.game.items import build_items_index

logger = logging.getLogger(__name__)

MAX_COMMANDS_PER_PACKET = 200
MAX_ARGS_PER_COMMAND = 16
MAX_COMMAND_NAME_LENGTH = 64


@dataclass
class DispatchResult:
    responses: List[Dict[str, Any]] = field(default_factory=list)
    applied_any: bool = False
    ignored: List[str] = field(default_factory=list)
    rejected: int = 0


def _resources_snapshot(player_data: Dict[str, Any]) -> Dict[str, Any]:
    info = player_data["playerInfo"]
    return {"pu": {"gold": info["gold"], "cash": info["cash"], "food": info["food"], "xp": info["xp"]}}


def _restore(player_data: Dict[str, Any], snapshot: Dict[str, Any]) -> None:
    player_data.clear()
    player_data.update(snapshot)


def dispatch_commands(
    user_id: int,
    player_data: Dict[str, Any],
    game_config: Dict[str, Any],
    commands: Any,
) -> DispatchResult:
    load_commands()
    items_index = build_items_index(game_config)
    result = DispatchResult()

    if not isinstance(commands, list):
        logger.warning("Player %s sent a packet whose 'commands' is not a list", user_id)
        return result
    if len(commands) > MAX_COMMANDS_PER_PACKET:
        logger.warning("Player %s sent %s commands, only the first %s are processed",
                       user_id, len(commands), MAX_COMMANDS_PER_PACKET)
        commands = commands[:MAX_COMMANDS_PER_PACKET]

    for cmd_data in commands:
        if not isinstance(cmd_data, dict):
            continue

        cmd = cmd_data.get("cmd")
        cmd_number = cmd_data.get("number")
        args = cmd_data.get("args", [])

        if not isinstance(cmd, str) or len(cmd) > MAX_COMMAND_NAME_LENGTH:
            cmd = None
        if isinstance(cmd_number, bool) or not isinstance(cmd_number, (int, type(None))):
            cmd_number = None

        handler = get_handler(cmd)
        ctx = CommandContext(
            user_id=user_id,
            cmd=cmd,
            number=cmd_number,
            args=args if isinstance(args, list) else [],
            player_data=player_data,
            game_config=game_config,
            items_index=items_index,
        )

        logger.info("Command %s | args=%s | number=%s", cmd, args, cmd_number)

        if handler is None:
            logger.warning("Command %s is not implemented, answering with a generic ok", cmd)
            result.ignored.append(str(cmd))
        else:
            result.applied_any = True
            snapshot = copy.deepcopy(player_data)
            try:
                if not isinstance(args, list) or len(args) > MAX_ARGS_PER_COMMAND:
                    raise CommandRejected("arguments must be a short list")
                check_json_depth(args, "arguments", max_depth=3, max_items=256)
                handler(ctx)
            except CommandRejected as exc:
                _restore(player_data, snapshot)
                ctx.result = RESULT_OK
                result.rejected += 1
                logger.warning("Rejected %s from player %s: %s", cmd, user_id, exc)
            except Exception:
                _restore(player_data, snapshot)
                ctx.result = RESULT_OK
                logger.exception("Command %s (number %s) failed", cmd, cmd_number)

        result.responses.append({
            "result": ctx.result if handler is not None else RESULT_OK,
            "number": cmd_number,
            "cmd": cmd,
            "resources": _resources_snapshot(player_data),
            "error": None,
        })

    return result
