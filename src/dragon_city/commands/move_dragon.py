import logging

from dragon_city.commands.base import CommandContext, command
from dragon_city.enums import Command

logger = logging.getLogger(__name__)


@command(Command.MOVE_DRAGON)
def handle(ctx: CommandContext) -> None:
    dragon_uid = int(ctx.args[0])
    new_habitat_id = int(ctx.args[1])

    for dragon in ctx.map.get("dragons", []):
        if int(dragon.get("id", 0)) == dragon_uid:
            old_habitat = dragon.get("habitatId")
            dragon["habitatId"] = new_habitat_id

            logger.info(
                "Moved dragon %s ('%s') from habitat %s to habitat %s",
                dragon_uid, dragon.get("name", "Unknown"), old_habitat, new_habitat_id,
            )
            return

    logger.warning("Dragon %s to move was not found", dragon_uid)
