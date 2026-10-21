import logging

from dragon_city.commands.base import CommandContext, command
from dragon_city.commands.validation import reject
from dragon_city.enums import Command

logger = logging.getLogger(__name__)

FIRST_BOX_PRICE = 20
NEXT_BOX_PRICE = 10
MAX_BOXES = 6


@command(Command.KOMPU_BOXES_OPEN_BOX)
def handle(ctx: CommandContext) -> None:
    private_state = ctx.private_state
    current_opened = private_state.get("kompuBoxesOpened", 0)

    if current_opened >= MAX_BOXES:
        reject("all the boxes are already open")

    if len(private_state.get("kompuBoxesDragons", [])) <= current_opened:
        reject("there is no kompu board to open a box from")

    ctx.pay(cash=FIRST_BOX_PRICE if current_opened == 0 else NEXT_BOX_PRICE)

    private_state["kompuBoxesOpened"] = current_opened + 1
    new_opened = private_state["kompuBoxesOpened"]

    kompu_dragons = private_state.get("kompuBoxesDragons", [])
    prize_dragon_id = "unknown"

    if len(kompu_dragons) >= new_opened:
        prize_dragon_id = kompu_dragons[new_opened - 1]

    logger.info("Opened box #%s, prize to claim: dragon %s", new_opened, prize_dragon_id)
