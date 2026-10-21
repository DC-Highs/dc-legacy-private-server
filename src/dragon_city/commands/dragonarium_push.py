import logging

from dragon_city.commands.base import CommandContext, command
from dragon_city.enums import Command, DragonariumTab
from dragon_city.game.dragonarium import TAB_COUNT, ensure_slots, tab_for_attributes

logger = logging.getLogger(__name__)


@command(Command.DRAGONARIUM_PUSH)
def handle(ctx: CommandContext) -> None:
    dragon_id = int(ctx.args[0])

    ensure_slots(ctx.private_state)

    if "dragonarium" not in ctx.private_state or len(ctx.private_state.get("dragonarium", [])) < TAB_COUNT:
        ctx.private_state["dragonarium"] = [[] for _ in range(TAB_COUNT)]

    active_dragons = ctx.player_data.get("map", {}).get("dragons", [])
    dragon_to_move = next((d for d in active_dragons if d.get("id") == dragon_id), None)

    if not dragon_to_move:
        logger.warning("Dragon with unique id %s not found on the player's map", dragon_id)
        return

    dragon_type = dragon_to_move.get("type")
    tab = DragonariumTab.ELEMENTAL

    item_data = next((item for item in ctx.game_config.get("items", []) if item.get("id") == dragon_type), None)
    if item_data:
        tab = tab_for_attributes(item_data.get("attributes", []))

    old_habitat = dragon_to_move.get("habitatId")
    dragon_to_move["habitatId"] = 0

    ctx.private_state["dragonarium"][tab].append(dragon_to_move)
    ctx.map["dragons"].remove(dragon_to_move)

    logger.info(
        "Pushed dragon '%s' (unique id %s, type %s) from habitat %s to dragonarium tab %s",
        dragon_to_move.get("name", "Unknown"), dragon_id, dragon_type, old_habitat, tab.name,
    )
