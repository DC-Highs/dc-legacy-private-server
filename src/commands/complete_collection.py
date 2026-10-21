import logging

from src.commands.base import CommandContext, command
from src.commands.validation import reject
from src.enums import Command, Resource

logger = logging.getLogger(__name__)

ACHIEVEMENT_POINTS = 75


@command(Command.COMPLETE_COLLECTION)
def handle(ctx: CommandContext) -> None:
    collection_id = ctx.int_arg(0, "collection id", 0, 100000)

    collection = next((c for c in ctx.game_config.get("collections", []) if c.get("id") == collection_id), None)
    if not collection:
        reject(f"collection {collection_id} does not exist in the game config")

    completed = ctx.private_state.setdefault("completedCollection", [])
    if collection_id in completed:
        reject(f"the player had already completed collection {collection_id}")

    # The player must own every dragon of the collection (the dragon book tracks that).
    owned = ctx.map["ownedDragons"]
    missing = [d for d in collection.get("dragon_ids", []) if str(d) not in owned]
    if missing:
        reject(f"collection {collection_id} is incomplete, missing dragons {missing}")

    completed.append(collection_id)

    rewards = collection.get("reward", {})
    col_name = collection.get("name", f"Collection {collection_id}")

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
