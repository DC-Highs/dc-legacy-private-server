import logging

from dragon_city.commands.base import CommandContext, command
from dragon_city.enums import Command, Resource
from dragon_city.game.breeding import FALLBACK_DRAGON_ID, build_dragon_db, get_breed_result

logger = logging.getLogger(__name__)

DEFAULT_BREEDING_SECONDS = 3600
DEFAULT_BOOST_COST = 5


@command(Command.BREED_DRAGON)
def handle(ctx: CommandContext) -> None:
    iso_id = str(ctx.args[0])
    parent1_id = int(ctx.args[1])
    parent2_id = int(ctx.args[2])
    use_gems = int(ctx.args[3])

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

    dragon1_type = None
    dragon2_type = None
    dragon1_level = 1
    dragon2_level = 1

    for dragon in ctx.player_data.get("map", {}).get("dragons", []):
        if dragon.get("id") == parent1_id:
            dragon1_type = dragon.get("type")
            dragon1_level = (dragon.get("xp", 0) // 4) + 1
        elif dragon.get("id") == parent2_id:
            dragon2_type = dragon.get("type")
            dragon2_level = (dragon.get("xp", 0) // 4) + 1

    dragon_db = build_dragon_db(ctx.game_config)

    if dragon1_type and dragon2_type:
        outcome_id = get_breed_result(dragon1_type, dragon2_type, dragon1_level, dragon2_level, dragon_db, boosted)
    else:
        logger.warning("Parents %s or %s not found on the map, falling back to Terra", parent1_id, parent2_id)
        outcome_id = FALLBACK_DRAGON_ID

    duration = DEFAULT_BREEDING_SECONDS
    if outcome_id in dragon_db:
        duration = dragon_db[outcome_id]["breeding_time"]

    if "work" not in ctx.map:
        ctx.map["work"] = {}

    ctx.map["work"][iso_id] = [parent1_id, parent2_id, current_ts, duration, outcome_id]

    if iso_id in ctx.map.get("items", {}):
        ctx.map["items"][iso_id][3] = current_ts

    logger.info(
        "Breeding in cave %s | parent types (%s, %s) | result %s (%s) | boosted=%s",
        iso_id, dragon1_type, dragon2_type, outcome_id, dragon_db.get(outcome_id, {}).get("name", "?"), boosted,
    )

    ctx.result = outcome_id
