"""Runs the commands of a ``packet.php`` request against a player save."""
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List

from dragon_city.commands.base import RESULT_OK, CommandContext, get_handler, load_commands
from dragon_city.game.items import build_items_index

logger = logging.getLogger(__name__)


@dataclass
class DispatchResult:
    responses: List[Dict[str, Any]] = field(default_factory=list)
    applied_any: bool = False
    ignored: List[str] = field(default_factory=list)


def _resources_snapshot(player_data: Dict[str, Any]) -> Dict[str, Any]:
    info = player_data["playerInfo"]
    return {"pu": {"gold": info["gold"], "cash": info["cash"], "food": info["food"], "xp": info["xp"]}}


def dispatch_commands(
    user_id: str,
    player_data: Dict[str, Any],
    game_config: Dict[str, Any],
    commands: List[Dict[str, Any]],
) -> DispatchResult:
    load_commands()
    items_index = build_items_index(game_config)
    result = DispatchResult()

    for cmd_data in commands:
        cmd = cmd_data.get("cmd")
        cmd_number = cmd_data.get("number")
        args = cmd_data.get("args", [])

        ctx = CommandContext(
            user_id=user_id,
            cmd=cmd,
            number=cmd_number,
            args=args,
            player_data=player_data,
            game_config=game_config,
            items_index=items_index,
        )

        logger.info("Command %s | args=%s | number=%s", cmd, args, cmd_number)

        handler = get_handler(cmd)
        if handler is None:
            logger.warning("Command %s is not implemented, answering with a generic ok", cmd)
            result.ignored.append(str(cmd))
        else:
            result.applied_any = True
            try:
                handler(ctx)
            except Exception:
                logger.exception("Command %s (number %s) failed", cmd, cmd_number)

        result.responses.append({
            "result": ctx.result if handler is not None else RESULT_OK,
            "number": cmd_number,
            "cmd": cmd,
            "resources": _resources_snapshot(player_data),
            "error": None,
        })

    return result
