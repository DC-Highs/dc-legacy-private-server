"""Achievement-points market: rotating offers paid with achievement points."""
import logging
import random
import time
from typing import Any, Dict, List, Set

from src import storage
from src.enums import GroupType, OfferType

logger = logging.getLogger(__name__)

MARKET_REFRESH_SECONDS = 6 * 60 * 60

RESOURCE_RULES = {
    OfferType.GOLD: {"min": 500000, "max": 40000000, "per_unit": 4000, "min_cost": 125, "max_cost": 10000},
    OfferType.FOOD: {"min": 350000, "max": 10000000, "per_unit": 1000, "min_cost": 350, "max_cost": 10000},
    OfferType.GEMS: {"min": 100, "max": 2500, "per_unit": 0.4, "min_cost": 250, "max_cost": 6250},
}

RESOURCE_STEPS = {OfferType.GOLD: 50000, OfferType.FOOD: 10000}

DRAGON_BASE_COST_BY_CATEGORY = {
    3: 4000,
    4: 7500,
    5: 15000,
}
DRAGON_BASE_COST_DEFAULT_STEP = 5000

ATTRIBUTE_SURCHARGE = {
    "e": 0, "f": 0, "w": 0, "p": 0, "el": 0, "m": 0,
    "d": 500, "li": 500, "i": 500,
    "wr": 1000,
    "pu": 2000,
    "l": 4000,
}


def ensure_private_state(player_data: Dict[str, Any]) -> Dict[str, Any]:
    if "privateState" not in player_data or not isinstance(player_data["privateState"], dict):
        player_data["privateState"] = {}
    if "achievement_points" not in player_data["privateState"]:
        player_data["privateState"]["achievement_points"] = 0
    return player_data


def _resource_cost(res_type: OfferType, amount: int) -> int:
    rule = RESOURCE_RULES[res_type]
    if res_type == OfferType.GEMS:
        cost = int(round(amount * rule["per_unit"]))
    else:
        cost = int(amount // rule["per_unit"])
    return max(rule["min_cost"], min(rule["max_cost"], cost))


def _roll_resource_offer(res_type: OfferType) -> Dict[str, Any]:
    rule = RESOURCE_RULES[res_type]
    if res_type == OfferType.GEMS:
        amount = random.randint(rule["min"], rule["max"])
    else:
        amount = random.randrange(rule["min"], rule["max"] + 1, RESOURCE_STEPS[res_type])
    cost = _resource_cost(res_type, amount)
    return {"type": res_type.value, "amount": amount, "cost": cost}


def _build_dragon_pool(config_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    return [
        item for item in config_data.get("items", [])
        if item.get("group_type") == GroupType.DRAGON and item.get("category", 0) >= 3
    ]


def _dragon_cost(item_cfg: Dict[str, Any]) -> int:
    category = item_cfg.get("category", 3)
    base = DRAGON_BASE_COST_BY_CATEGORY.get(category)
    if base is None:
        base = 15000 + max(0, category - 5) * DRAGON_BASE_COST_DEFAULT_STEP
    surcharge = sum(ATTRIBUTE_SURCHARGE.get(attr, 0) for attr in item_cfg.get("attributes", []))
    return base + surcharge


def _roll_dragon_offer(dragon_pool: List[Dict[str, Any]], already_chosen_ids: Set[int]) -> Dict[str, Any]:
    candidates = [d for d in dragon_pool if d["id"] not in already_chosen_ids]
    if not candidates:
        candidates = dragon_pool
    item_cfg = random.choice(candidates)
    return {
        "type": OfferType.DRAGON.value,
        "dragon_id": item_cfg["id"],
        "name": item_cfg.get("name"),
        "img": item_cfg.get("img_name"),
        "category": item_cfg.get("category"),
        "attributes": item_cfg.get("attributes", []),
        "cost": _dragon_cost(item_cfg),
    }


def save_market(user_id: Any, market_data: Dict[str, Any]) -> None:
    storage.save_market(user_id, market_data)


def generate_market_offers(user_id: Any) -> Dict[str, Any]:
    config_data = storage.load_base_config()
    dragon_pool = _build_dragon_pool(config_data)

    dragon_offers = []
    chosen_dragon_ids: Set[int] = set()
    for _ in range(2):
        d_offer = _roll_dragon_offer(dragon_pool, chosen_dragon_ids)
        chosen_dragon_ids.add(d_offer["dragon_id"])
        dragon_offers.append(d_offer)

    gold_offers = [_roll_resource_offer(OfferType.GOLD) for _ in range(2)]
    food_offers = [_roll_resource_offer(OfferType.FOOD) for _ in range(2)]
    gems_offers = [_roll_resource_offer(OfferType.GEMS) for _ in range(2)]

    offers = [
        dragon_offers[0], gold_offers[0], food_offers[0], gems_offers[0],
        dragon_offers[1], gold_offers[1], food_offers[1], gems_offers[1],
    ]

    for idx, offer in enumerate(offers, start=1):
        offer["id"] = idx
        offer["sold"] = False

    market_data = {
        "user_id": str(user_id),
        "generated_at": int(time.time()),
        "next_refresh_at": int(time.time()) + MARKET_REFRESH_SECONDS,
        "offers": offers,
    }

    save_market(user_id, market_data)
    logger.info("Generated %s market offers for player %s", len(offers), user_id)

    return market_data


def load_or_create_market(user_id: Any) -> Dict[str, Any]:
    market_data = storage.get_market(user_id)

    if not market_data:
        return generate_market_offers(user_id)

    if int(time.time()) >= market_data.get("next_refresh_at", 0):
        return generate_market_offers(user_id)

    return market_data


def grant_dragon_to_player(player_data: Dict[str, Any], offer: Dict[str, Any]) -> None:
    dragon_iid = offer.get("dragon_id")

    if not dragon_iid:
        logger.error("The offer does not contain a valid dragon id")
        return

    if "map" not in player_data or isinstance(player_data["map"], list):
        player_data["map"] = {}

    if "store" not in player_data["map"] or isinstance(player_data["map"]["store"], list):
        player_data["map"]["store"] = {"items": {}, "dragons": []}

    if "dragons" not in player_data["map"]["store"] or not isinstance(player_data["map"]["store"]["dragons"], list):
        player_data["map"]["store"]["dragons"] = []

    player_data["map"]["store"]["dragons"].append({"iid": dragon_iid, "lvl": 0})
