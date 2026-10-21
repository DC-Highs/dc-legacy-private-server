import json
import logging

from src import storage
from src.commands.base import CommandContext, command
from src.commands.validation import check_json_depth, reject
from src.enums import Command

logger = logging.getLogger(__name__)

MAX_CLICKS_PER_ASSIST = 50


@command(Command.ASSIST_NEIGHBOR)
def handle(ctx: CommandContext) -> None:
    target_id = ctx.int_arg(0, "neighbor id", 1)
    raw_clicks = ctx.text_arg(1, "clicks", 256, allow_empty=True)

    if target_id == ctx.user_id:
        reject("a player cannot assist themselves")
    if not storage.player_exists(target_id):
        reject(f"neighbor {target_id} does not exist")

    try:
        clicks = json.loads(raw_clicks, parse_constant=lambda _c: reject("clicks has an invalid number"))
    except ValueError:
        reject("clicks is not valid JSON")
    if not isinstance(clicks, list) or not clicks or len(clicks) > MAX_CLICKS_PER_ASSIST:
        reject(f"clicks must be a list of 1 to {MAX_CLICKS_PER_ASSIST} entries")
    check_json_depth(clicks, "clicks", max_depth=2, max_items=MAX_CLICKS_PER_ASSIST * 4)

    # The neighbour may be playing right now, so the assist is queued and merged into their
    # save the next time they load it, instead of rewriting their save from here.
    storage.add_pending_assist(target_id, ctx.user_id, clicks)

    logger.info("Helped neighbor %s", target_id)
