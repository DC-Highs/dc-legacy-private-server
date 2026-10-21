import logging

from src.commands.base import CommandContext, command
from src.commands.validation import reject
from src.enums import Command, GroupType
from src.game.items import get_item_config

logger = logging.getLogger(__name__)


@command(Command.MOVE_DRAGON)
def handle(ctx: CommandContext) -> None:
    dragon = ctx.find_dragon(ctx.uid_arg(0, "dragon uid"))
    new_habitat_id = ctx.int_arg(1, "habitat", 1)

    habitat = ctx.map_item(str(new_habitat_id))
    habitat_cfg = get_item_config(ctx.game_config, habitat[0])
    if not habitat_cfg or habitat_cfg.get("group_type") != GroupType.HABITAT:
        reject(f"object {new_habitat_id} is not a habitat")

    old_habitat = dragon.get("habitatId")
    dragon["habitatId"] = new_habitat_id

    logger.info(
        "Moved dragon %s ('%s') from habitat %s to habitat %s",
        dragon.get("id"), dragon.get("name", "Unknown"), old_habitat, new_habitat_id,
    )
