import logging

from dragon_city.commands.base import CommandContext, command
from dragon_city.commands.validation import reject
from dragon_city.enums import Command, DragonariumTab, Resource
from dragon_city.game.dragonarium import MAX_SLOTS_PER_TAB, ensure_slots

logger = logging.getLogger(__name__)

# Gems needed to add a slot, indexed by dragonarium tab.
SLOT_COSTS = (2, 2, 3, 4, 5)


@command(Command.DRAGONARIUM_ADD)
def handle(ctx: CommandContext) -> None:
    slot_index = ctx.int_arg(0, "slot", 0, len(SLOT_COSTS) - 1)
    slot_name = DragonariumTab(slot_index).name.title()

    slots = ensure_slots(ctx.private_state)
    if slots[slot_index] >= MAX_SLOTS_PER_TAB:
        reject(f"the {slot_name} tab already has the maximum number of slots")

    ctx.pay(cash=SLOT_COSTS[slot_index])
    slots[slot_index] += 1

    logger.info("Added a slot to the %s tab", slot_name)
    logger.info("Slots in the %s tab: %s", slot_name, slots[slot_index])
    logger.info("Remaining gems: %s", ctx.info[Resource.CASH])
