"""Black market ("Kompu") boxes and offers."""
import logging
import random
from typing import Any, Dict, List, Tuple

from dragon_city.enums import GroupType
from dragon_city.storage import save_kompu_offers

logger = logging.getLogger(__name__)

FALLBACK_COMMON_DRAGON_ID = 1011
FALLBACK_RARE_DRAGON_ID = 1041

OFFER_DURATION_SECONDS = 259200
MIN_COOLDOWN_SECONDS = 259200
MAX_COOLDOWN_SECONDS = 604800
UNIQUE_DRAGON_CHANCE_PERCENT = 10
UNIQUE_DRAGON_CHANCE = 0.10


def generate_black_market_boxes(user_game_config: Dict[str, Any]) -> Tuple[int, List[int], List[int]]:
    cat_2_3, cat_3_4_5 = [], []
    cat_4, cat_5 = [], []

    for item in user_game_config.get("items", []):
        if item.get("group_type") == GroupType.DRAGON and "category" in item:
            cat = item["category"]
            d_id = item["id"]
            if cat in [2, 3]:
                cat_2_3.append(d_id)
            if cat == 4:
                cat_4.append(d_id)
            if cat == 5:
                cat_5.append(d_id)
            if cat in [3, 4, 5]:
                cat_3_4_5.append(d_id)

    unique_dragon = random.choice(cat_3_4_5) if cat_3_4_5 else FALLBACK_RARE_DRAGON_ID

    kompu_boxes: List[int] = []

    if len(cat_2_3) >= 3:
        kompu_boxes.extend(random.sample(cat_2_3, 3))
    else:
        kompu_boxes.extend(cat_2_3)
        while len(kompu_boxes) < 3:
            kompu_boxes.append(FALLBACK_COMMON_DRAGON_ID)

    if len(cat_4) >= 2:
        kompu_boxes.extend(random.sample(cat_4, 2))
    else:
        kompu_boxes.extend(cat_4)
        while len(kompu_boxes) < 5:
            kompu_boxes.append(FALLBACK_COMMON_DRAGON_ID)

    unique_roll = random.randint(1, 100)
    if unique_roll <= UNIQUE_DRAGON_CHANCE_PERCENT:
        kompu_boxes.append(unique_dragon)
    else:
        kompu_boxes.append(random.choice(cat_5) if cat_5 else FALLBACK_RARE_DRAGON_ID)

    kompu_shuffled = list(kompu_boxes)
    random.shuffle(kompu_shuffled)

    return unique_dragon, kompu_boxes, kompu_shuffled


def build_kompu_offers_payload(
    user_game_config: Dict[str, Any], start_timestamp: int, unique_dragon: int
) -> List[Dict[str, Any]]:
    cat_1, cat_2_3, cat_4_5, cat_3_4_5 = [], [], [], []
    for item in user_game_config.get("items", []):
        if item.get("group_type") == GroupType.DRAGON and "category" in item:
            cat = item["category"]
            d_id = item["id"]
            if cat == 1:
                cat_1.append(d_id)
            elif cat in [2, 3]:
                cat_2_3.append(d_id)
            if cat in [4, 5]:
                cat_4_5.append(d_id)
            if cat in [3, 4, 5]:
                cat_3_4_5.append(d_id)

    pool_x2 = random.sample(cat_1, min(10, len(cat_1))) if cat_1 else [FALLBACK_COMMON_DRAGON_ID]
    pool_x3 = random.sample(cat_2_3, min(10, len(cat_2_3))) if cat_2_3 else [FALLBACK_COMMON_DRAGON_ID]
    pool_x4 = random.sample(cat_4_5, min(7, len(cat_4_5))) if cat_4_5 else [FALLBACK_RARE_DRAGON_ID]
    pool_x5 = random.sample(cat_3_4_5, min(5, len(cat_3_4_5))) if cat_3_4_5 else [FALLBACK_RARE_DRAGON_ID]

    return [{
        "id": 1,
        "starts_at": start_timestamp,
        "duration": OFFER_DURATION_SECONDS,
        "game_type": 4,
        "resetable": 0,
        "pick_prize": 0,
        "hurry_up_cost": 10,
        "timer_between": 21600,
        "viral_icon": [],
        "rewards": {
            "uniqueDragonId": unique_dragon,
            "prizes": [pool_x2, pool_x3, pool_x4, pool_x5],
        },
    }]


def schedule_black_market(private_state: Dict[str, Any], game_config: Dict[str, Any], current_ts: int, delay: int) -> None:
    """Set the black market window and roll its boxes (used when it is first unlocked)."""
    private_state["BlackMarketTs"] = current_ts
    private_state["BlackMarketStart"] = current_ts + delay
    private_state["BlackMarketEnd"] = private_state["BlackMarketStart"] + OFFER_DURATION_SECONDS

    unique_dragon, boxes, shuffled_boxes = generate_black_market_boxes(game_config)
    private_state["BlackMarketUniqueDragon"] = unique_dragon
    private_state["kompuBoxesDragons"] = boxes
    private_state["kompuBoxesShuffledDragons"] = shuffled_boxes


def roll_kompu_pool(game_config: Dict[str, Any]) -> Tuple[List[int], bool]:
    """Roll the six-dragon pool of a new kompu board.

    Returns the pool and whether the unique dragon of the current offer made it in.
    """
    kompu_offers = game_config.get("kompu_offers", [])
    unique_dragon_id = None
    if kompu_offers and isinstance(kompu_offers, list):
        rewards = kompu_offers[0].get("rewards", {})
        if isinstance(rewards, dict):
            unique_dragon_id = rewards.get("uniqueDragonId")

    dragons_cat_234, dragons_cat_4, dragons_cat_5 = [], [], []

    for item in game_config.get("items", []):
        if item.get("group_type") == GroupType.DRAGON:
            cat = item.get("category", 1)
            d_id = item.get("id")
            if cat in [2, 3, 4]:
                dragons_cat_234.append(d_id)
            if cat == 4:
                dragons_cat_4.append(d_id)
            if cat == 5:
                dragons_cat_5.append(d_id)

    pool_dragons: List[int] = []

    pool_dragons.extend(random.sample(dragons_cat_234, min(4, len(dragons_cat_234))))
    while len(pool_dragons) < 4:
        pool_dragons.append(random.choice(dragons_cat_234))

    pool_dragons.append(random.choice(dragons_cat_4))

    unique_included = False
    if unique_dragon_id and random.random() <= UNIQUE_DRAGON_CHANCE:
        pool_dragons.append(unique_dragon_id)
        unique_included = True
    else:
        pool_dragons.append(random.choice(dragons_cat_5))

    return pool_dragons, unique_included


def check_and_update_black_market(
    player_data: Dict[str, Any], user_id: str, game_config: Dict[str, Any]
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    current_ts = player_data.get("timestamp", 0)
    private_state = player_data["privateState"]

    bm_start = int(private_state.get("BlackMarketStart") or 0)
    bm_end = int(private_state.get("BlackMarketEnd") or 0)

    if bm_start == 0 or bm_end == 0:
        return player_data, game_config

    config_modified = False

    if current_ts >= bm_end:
        game_config["kompu_offers"] = []
        private_state["BlackMarketTs"] = current_ts

        new_cooldown = random.randint(MIN_COOLDOWN_SECONDS, MAX_COOLDOWN_SECONDS)
        private_state["BlackMarketStart"] = current_ts + new_cooldown
        private_state["BlackMarketEnd"] = private_state["BlackMarketStart"] + OFFER_DURATION_SECONDS

        unique_dragon, boxes, shuffled_boxes = generate_black_market_boxes(game_config)
        private_state["BlackMarketUniqueDragon"] = int(unique_dragon)
        private_state["kompuBoxesDragons"] = boxes
        private_state["kompuBoxesShuffledDragons"] = shuffled_boxes

        config_modified = True
        logger.info(
            "Black market expired for %s, next one in %s days, new boxes waiting: %s",
            user_id, new_cooldown // 86400, boxes,
        )

    elif bm_start <= current_ts < bm_end:
        if not game_config.get("kompu_offers"):
            unique_dragon = int(player_data.get("BlackMarketUniqueDragon", FALLBACK_RARE_DRAGON_ID))
            game_config["kompu_offers"] = build_kompu_offers_payload(game_config, bm_start, unique_dragon)

            config_modified = True
            logger.info("Black market is now visible in the HUD of player %s", user_id)

    if config_modified:
        save_kompu_offers(user_id, game_config["kompu_offers"])

    return player_data, game_config
