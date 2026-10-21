import logging

from src.commands.base import CommandContext, command
from src.commands.validation import reject
from src.enums import Command, Resource
from src.game.breeding import build_dragon_db, get_breed_result

logger = logging.getLogger(__name__)

DEFAULT_BREEDING_SECONDS = 3600
DEFAULT_BOOST_COST = 5


@command(Command.BREED_DRAGON)
def handle(ctx: CommandContext) -> None:
    iso_id = ctx.iso_arg(0, "breeding cave")
    parent1_id = ctx.uid_arg(1, "first parent")
    parent2_id = ctx.uid_arg(2, "second parent")
    use_gems = ctx.flag_arg(3, "use gems")

    ctx.map_item(iso_id)
    if parent1_id == parent2_id:
        reject("a dragon cannot breed with itself")
    parent1 = ctx.find_dragon(parent1_id)
    parent2 = ctx.find_dragon(parent2_id)

    current_ts = ctx.server_ts
    info = ctx.info

    boosted = False
    if use_gems == 1:
        boost_cost = ctx.game_config.get("globals", {}).get("RARITY_BOOST_COST", {}).get("value", DEFAULT_BOOST_COST)
        if info[Resource.CASH] >= int(boost_cost):
            info[Resource.CASH] -= int(boost_cost)
            boosted = True
        else:
            logger.warning("Not enough gems for the rarity boost")

    dragon1_type = parent1.get("type")
    dragon2_type = parent2.get("type")
    dragon1_level = (parent1.get("xp", 0) // 4) + 1
    dragon2_level = (parent2.get("xp", 0) // 4) + 1

    dragon_db = build_dragon_db(ctx.game_config)
    outcome_id = get_breed_result(dragon1_type, dragon2_type, dragon1_level, dragon2_level, dragon_db, boosted)

    duration = DEFAULT_BREEDING_SECONDS
    if outcome_id in dragon_db:
        duration = dragon_db[outcome_id]["breeding_time"]

    ctx.map["work"][iso_id] = [parent1_id, parent2_id, current_ts, duration, outcome_id]
    ctx.map["items"][iso_id][3] = current_ts

    logger.info(
        "Breeding in cave %s | parent types (%s, %s) | result %s (%s) | boosted=%s",
        iso_id, dragon1_type, dragon2_type, outcome_id, dragon_db.get(outcome_id, {}).get("name", "?"), boosted,
    )

    ctx.result = outcome_id
