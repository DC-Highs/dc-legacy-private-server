import logging

from dragon_city.commands.base import CommandContext, command
from dragon_city.enums import Command, Resource

logger = logging.getLogger(__name__)

ACHIEVEMENT_POINTS = 75


@command(Command.COMPLETE_COLLECTION)
def handle(ctx: CommandContext) -> None:
    collection_id = int(ctx.args[0])

    if "completedCollection" not in ctx.private_state:
        ctx.private_state["completedCollection"] = []

    completed = ctx.private_state["completedCollection"]
    if collection_id in completed:
        logger.warning("The player had already completed collection %s", collection_id)
        return

    completed.append(collection_id)

    collection_found = None
    for collection in ctx.game_config.get("collections", []):
        if collection.get("id") == collection_id:
            collection_found = collection
            break

    if not collection_found:
        logger.warning("Collection %s was registered but does not exist in the game config", collection_id)
        return

    rewards = collection_found.get("reward", {})
    col_name = collection_found.get("name", f"Collection {collection_id}")

    gold_reward = rewards.get("g", 0)
    food_reward = rewards.get("f", 0)
    cash_reward = rewards.get("c", 0)
    xp_reward = rewards.get("x", 0)

    info = ctx.info
    info[Resource.GOLD] += gold_reward
    info[Resource.FOOD] += food_reward
    info[Resource.CASH] += cash_reward
    info[Resource.XP] += xp_reward
    ctx.private_state["achievement_points"] += ACHIEVEMENT_POINTS

    logger.info("Collection '%s' (id %s) completed", col_name, collection_id)
    logger.info(
        "Rewards applied -> gold: +%s, food: +%s, gems: +%s, xp: +%s, points: +%s",
        gold_reward, food_reward, cash_reward, xp_reward, ACHIEVEMENT_POINTS,
    )
