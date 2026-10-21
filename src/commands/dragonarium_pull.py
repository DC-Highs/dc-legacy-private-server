import logging

from src.commands.base import CommandContext, command
from src.commands.validation import reject
from src.enums import Command, GroupType
from src.game.dragonarium import ensure_tabs
from src.game.items import get_item_config

logger = logging.getLogger(__name__)


@command(Command.DRAGONARIUM_PULL)
def handle(ctx: CommandContext) -> None:
    category_index = ctx.int_arg(1, "tab", 0, 1000)
    dragon_index = ctx.int_arg(2, "position", 0, 100000)
    target_habitat_id = ctx.int_arg(3, "habitat", 1)

    habitat = ctx.map_item(str(target_habitat_id))
    habitat_cfg = get_item_config(ctx.game_config, habitat[0])
    if not habitat_cfg or habitat_cfg.get("group_type") != GroupType.HABITAT:
        reject(f"object {target_habitat_id} is not a habitat")

    dragonarium = ensure_tabs(ctx.private_state)

    if category_index >= len(dragonarium):
        reject(f"tab index {category_index} does not exist in the dragonarium")

    tab_dragons = dragonarium[category_index]

    if dragon_index >= len(tab_dragons):
        reject(f"dragon index {dragon_index} is out of range for tab {category_index}")

    dragon_to_move = tab_dragons.pop(dragon_index)
    dragon_to_move["habitatId"] = target_habitat_id
    ctx.map["dragons"].append(dragon_to_move)

    logger.info(
        "Pulled dragon '%s' (unique id %s) from tab %s position %s to habitat %s",
        dragon_to_move.get("name", "Unknown"), dragon_to_move.get("id", "n/a"),
        category_index, dragon_index, target_habitat_id,
    )
