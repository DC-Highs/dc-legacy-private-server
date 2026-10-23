"""Assigning the player's own friends as workers of the Allies Market.

The Allies Market is item 79 (``ALLIES_MARKET`` in the game config, ``group_type``
``SOCIAL BUILDING``; the sprite ships as ``0079_allies_market.swf``, though this config
snapshot's own ``name`` field for it reads "Dragon Market" instead). It has 6 worker slots
(``social_items`` id 79 lists 6 named roles). This command only sets which friends fill those
slots, the same "store a roster, grant nothing" shape as ``set_attack_team``.

It does not pay out gold or food: the production formula and the command that would collect it
(``RESOURCES_MARKET_PER_ALLY`` in the config hints at one) were not found anywhere in the save
or in the commands already implemented, so nothing is paid until that is confirmed. See
docs/commands-roadmap.md.
"""
import json
import logging

from src import friends
from src.commands.base import CommandContext, command
from src.commands.validation import check_json_depth, reject, to_int
from src.db.postgres import session_scope
from src.enums import Command, GroupType
from src.game.items import get_item_config

logger = logging.getLogger(__name__)

ALLIES_MARKET_ITEM_ID = 79
MAX_ALLY_WORKERS = 6


@command(Command.SET_RESOURCE_ALLIES)
def handle(ctx: CommandContext) -> None:
    iso_id = ctx.iso_arg(0)
    raw_ids = ctx.text_arg(1, "ally ids", 256, allow_empty=True)

    item_data = ctx.map_item(iso_id)
    if item_data[0] != ALLIES_MARKET_ITEM_ID:
        reject(f"object {iso_id} is not the Allies Market")

    item_cfg = get_item_config(ctx.game_config, item_data[0])
    if not item_cfg or item_cfg.get("group_type") != GroupType.SOCIAL_BUILDING:
        reject(f"object {iso_id} is not a social building")

    try:
        ally_ids = json.loads(raw_ids, parse_constant=lambda _c: reject("ally ids has an invalid number"))
    except ValueError:
        reject("ally ids is not valid JSON")
    if not isinstance(ally_ids, list) or len(ally_ids) > MAX_ALLY_WORKERS:
        reject(f"the Allies Market has at most {MAX_ALLY_WORKERS} worker slots")
    check_json_depth(ally_ids, "ally ids", max_depth=1, max_items=MAX_ALLY_WORKERS + 1)

    friend_ids = []
    for raw_id in ally_ids:
        friend_id = to_int(raw_id, "ally id", 1)
        if friend_id in friend_ids:
            reject(f"friend {friend_id} is assigned twice")
        friend_ids.append(friend_id)

    if friend_ids:
        with session_scope() as session:
            for friend_id in friend_ids:
                if not friends.are_friends(session, ctx.user_id, friend_id):
                    reject(f"{friend_id} is not one of the player's neighbours")

    while len(item_data) <= 6:
        item_data.append({})
    if not isinstance(item_data[6], dict):
        item_data[6] = {}
    item_data[6]["allies"] = friend_ids

    logger.info("Allies Market %s workers set: %s", iso_id, friend_ids)
