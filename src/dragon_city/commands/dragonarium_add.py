import logging

from dragon_city.commands.base import CommandContext, command
from dragon_city.enums import Command, DragonariumTab, Resource
from dragon_city.game.dragonarium import ensure_slots

logger = logging.getLogger(__name__)

# Gems needed to add a slot, indexed by dragonarium tab.
SLOT_COSTS = (2, 2, 3, 4, 5)


@command(Command.DRAGONARIUM_ADD)
def handle(ctx: CommandContext) -> None:
    slot_index = int(ctx.args[0])

    slot_cost = SLOT_COSTS[slot_index]
    ctx.info[Resource.CASH] -= slot_cost

    try:
        slot_name = DragonariumTab(slot_index).name.title()
    except ValueError:
        slot_name = f"Unknown ({slot_index})"

    slots = ensure_slots(ctx.private_state)

    if not 0 <= slot_index < len(slots):
        logger.warning("Slot index %s is out of range for the dragonarium", slot_index)
        return

    slots[slot_index] += 1

    logger.info("Added a slot to the %s tab", slot_name)
    logger.info("Slots in the %s tab: %s", slot_name, slots[slot_index])
    logger.info("Remaining gems: %s", ctx.info[Resource.CASH])
