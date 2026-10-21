import logging

from dragon_city.commands.base import CommandContext, command
from dragon_city.enums import Command

logger = logging.getLogger(__name__)


@command(Command.DRAGONARIUM_PULL)
def handle(ctx: CommandContext) -> None:
    category_index = int(ctx.args[1])
    dragon_index = int(ctx.args[2])
    target_habitat_id = int(ctx.args[3])

    dragonarium = ctx.player_data.get("privateState", {}).get("dragonarium", [])

    if not 0 <= category_index < len(dragonarium):
        logger.warning("Tab index %s does not exist in the dragonarium", category_index)
        return

    tab_dragons = dragonarium[category_index]

    if not 0 <= dragon_index < len(tab_dragons):
        logger.warning("Dragon index %s is out of range for tab %s", dragon_index, category_index)
        return

    dragon_to_move = tab_dragons.pop(dragon_index)
    dragon_to_move["habitatId"] = target_habitat_id

    if "map" not in ctx.player_data:
        ctx.player_data["map"] = {}
    if "dragons" not in ctx.map:
        ctx.map["dragons"] = []

    ctx.map["dragons"].append(dragon_to_move)

    logger.info(
        "Pulled dragon '%s' (unique id %s) from tab %s position %s to habitat %s",
        dragon_to_move.get("name", "Unknown"), dragon_to_move.get("id", "n/a"),
        category_index, dragon_index, target_habitat_id,
    )
