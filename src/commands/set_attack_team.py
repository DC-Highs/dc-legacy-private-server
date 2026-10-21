import json
import logging

from src.commands.base import CommandContext, command
from src.commands.validation import check_json_depth, reject, to_uid
from src.enums import Command

logger = logging.getLogger(__name__)

MAX_TEAM_SIZE = 6
MAX_TEAM_TYPES = 8


@command(Command.SET_ATTACK_TEAM)
def handle(ctx: CommandContext) -> None:
    team_type = ctx.text_arg(0, "team type", 16)
    raw_ids = ctx.text_arg(1, "team ids", 256, allow_empty=True)

    try:
        team_ids = json.loads(raw_ids, parse_constant=lambda _c: reject("team ids has an invalid number"))
    except ValueError:
        reject("team ids is not valid JSON")
    if not isinstance(team_ids, list) or len(team_ids) > MAX_TEAM_SIZE:
        reject(f"a team has at most {MAX_TEAM_SIZE} dragons")
    check_json_depth(team_ids, "team ids", max_depth=1, max_items=MAX_TEAM_SIZE + 1)

    owned = {str(d.get("id")) for d in ctx.map["dragons"]}
    formatted_team = []
    for dragon_id in team_ids:
        dragon_id = to_uid(dragon_id, "dragon id")
        if str(dragon_id) not in owned:
            reject(f"dragon {dragon_id} is not on the map")
        formatted_team.append({"id": dragon_id})

    teams = ctx.private_state.get("teams")
    if not isinstance(teams, dict):
        teams = ctx.private_state["teams"] = {}
    if team_type not in teams and len(teams) >= MAX_TEAM_TYPES:
        reject("too many team types")

    teams[team_type] = formatted_team
    logger.info("Attack team '%s' set: %s", team_type, formatted_team)
