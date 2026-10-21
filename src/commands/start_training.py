import logging
import time

from src.commands.base import CommandContext, command
from src.commands.validation import reject
from src.enums import Command
from src.game.items import get_item_config
from src.game.training import ATTACK_SLOTS

logger = logging.getLogger(__name__)


@command(Command.START_TRAINING)
def handle(ctx: CommandContext) -> None:
    building_uid = ctx.iso_arg(0, "training building")
    dragon_uid = ctx.uid_arg(1, "dragon uid")
    attack_id = ctx.int_arg(2, "attack id", 1, 100000)
    attack_pos = ctx.int_arg(3, "attack slot", 0, ATTACK_SLOTS - 1)

    ctx.map_item(building_uid)
    if building_uid in ctx.map["work"]:
        reject(f"building {building_uid} is already busy")

    dragon = ctx.find_dragon(dragon_uid)
    if str(attack_id) not in ctx.game_config.get("attacks", {}):
        reject(f"attack {attack_id} does not exist")
    dragon_cfg = get_item_config(ctx.game_config, dragon.get("type")) or {}
    trainable = dragon_cfg.get("trainable_attacks")
    if isinstance(trainable, list) and trainable and attack_id not in trainable:
        reject(f"dragon {dragon_uid} cannot learn attack {attack_id}")

    ctx.map["work"][building_uid] = [dragon_uid, attack_id, int(time.time()), attack_pos]
    dragon["work_id"] = int(building_uid)

    logger.info("Dragon %s (id %s) entered the training center", dragon.get("name", "Unknown"), dragon_uid)
    logger.info("Building %s is training attack %s in slot %s", building_uid, attack_id, attack_pos)
