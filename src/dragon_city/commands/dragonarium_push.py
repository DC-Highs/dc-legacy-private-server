import logging

from dragon_city.commands.base import CommandContext, command
from dragon_city.commands.validation import reject
from dragon_city.enums import Command, DragonariumTab
from dragon_city.game.dragonarium import has_free_slot, tab_for_attributes
from dragon_city.game.items import get_item_config

logger = logging.getLogger(__name__)


@command(Command.DRAGONARIUM_PUSH)
def handle(ctx: CommandContext) -> None:
    dragon_to_move = ctx.find_dragon(ctx.uid_arg(0, "dragon uid"))
    dragon_type = dragon_to_move.get("type")

    item_data = get_item_config(ctx.game_config, dragon_type)
    tab = tab_for_attributes(item_data.get("attributes", [])) if item_data else DragonariumTab.ELEMENTAL

    if not has_free_slot(ctx.private_state, tab):
        reject(f"the dragonarium tab {tab.name} is full")

    old_habitat = dragon_to_move.get("habitatId")
    dragon_to_move["habitatId"] = 0

    ctx.private_state["dragonarium"][tab].append(dragon_to_move)
    ctx.map["dragons"].remove(dragon_to_move)

    logger.info(
        "Pushed dragon '%s' (unique id %s, type %s) from habitat %s to dragonarium tab %s",
        dragon_to_move.get("name", "Unknown"), dragon_to_move.get("id"), dragon_type, old_habitat, tab.name,
    )
