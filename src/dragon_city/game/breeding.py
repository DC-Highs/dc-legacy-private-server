"""Breeding engine: decides which dragon a pair of parents produces."""
import logging
import random
from typing import Any, Dict, Set

from dragon_city.enums import DragonAttribute as Attr
from dragon_city.enums import GroupType

logger = logging.getLogger(__name__)

FALLBACK_DRAGON_ID = 1011  # Terra

WEIGHT_DIFFICULTY = {1: 55, 2: 25, 3: 5}
WEIGHT_DIFFICULTY_BOOSTED = {1: 40, 2: 35, 3: 25}

CATEGORY_MULTIPLIER = {
    1: 0.65,
    2: 0.90,
    3: 0.55,
    4: 0.22,
    5: 0.15,
}

LEGENDARY_COMBOS_BY_ATTRS = {
    frozenset({Attr.WATER, Attr.PLANT, Attr.ICE, Attr.FIRE}): [1041, 1054],
    frozenset({Attr.EARTH, Attr.METAL, Attr.FIRE, Attr.ICE}): [1041, 1052, 1053, 1054],
    frozenset({Attr.WATER, Attr.PLANT, Attr.FIRE, Attr.ICE}): [1052, 1053],
    frozenset({Attr.WATER, Attr.DARK}): [1052],
}

LEGENDARY_FROM_COMBO_CHANCE = 15.0

PURE_DRAGON_BASE_ID = 1081
PURE_CHANCE_BASE = 3.0
PURE_CHANCE_BOOSTED = 5.0

PURE_ELEMENT_IDS = [1082, 1083, 1084, 1085, 1086, 1087, 1088, 1089]
PURE_ELEMENT_CHANCE_BASE = 5.0
PURE_ELEMENT_CHANCE_BOOSTED = 7.5

DragonDb = Dict[int, Dict[str, Any]]


def build_dragon_db(config: Dict[str, Any]) -> DragonDb:
    db: DragonDb = {}
    for item in config.get("items", []):
        if item.get("group_type") != GroupType.DRAGON:
            continue
        db[item["id"]] = {
            "name": item.get("name", "Unknown"),
            "attributes": set(item.get("attributes", [])),
            "difficulty": item.get("difficulty", 3),
            "category": item.get("category", 1),
            "breeding_time": item.get("breeding_time", 86400),
            "breedable": item.get("breedable", 0),
        }
    return db


def get_breed_result(
    dragon1_type: int,
    dragon2_type: int,
    level1: int,
    level2: int,
    dragon_db: DragonDb,
    boosted: bool = False,
) -> int:
    if dragon1_type not in dragon_db or dragon2_type not in dragon_db:
        logger.warning("Unknown parent types (%s, %s), falling back to Terra", dragon1_type, dragon2_type)
        return FALLBACK_DRAGON_ID

    parent1 = dragon_db[dragon1_type]
    parent2 = dragon_db[dragon2_type]
    pool: Set[str] = parent1["attributes"] | parent2["attributes"]

    is_leg1 = Attr.LEGENDARY in parent1["attributes"]
    is_leg2 = Attr.LEGENDARY in parent2["attributes"]

    if is_leg1 != is_leg2:
        logger.info("Legendary + common cross, picking a random dragon from the database")
        valid_any = [
            dtype for dtype, ddata in dragon_db.items()
            if ddata["breedable"] > 0 and level1 >= ddata["breedable"] and level2 >= ddata["breedable"]
        ]
        if valid_any:
            chosen = random.choice(valid_any)
            logger.info("Random result: dragon %s (%s)", chosen, dragon_db[chosen]["name"])
            return chosen

    both_legendary = is_leg1 and is_leg2
    if both_legendary:
        pure_chance = PURE_CHANCE_BOOSTED if boosted else PURE_CHANCE_BASE
        pe_chance = PURE_ELEMENT_CHANCE_BOOSTED if boosted else PURE_ELEMENT_CHANCE_BASE

        roll = random.uniform(0, 100)

        if roll < pure_chance:
            if PURE_DRAGON_BASE_ID in dragon_db:
                logger.info("Pure base dragon %s", PURE_DRAGON_BASE_ID)
                return PURE_DRAGON_BASE_ID

        elif roll < pure_chance + pe_chance:
            pure_with_el = [
                did for did, dd in dragon_db.items()
                if Attr.PURE in dd["attributes"] and len(dd["attributes"]) > 1
                and dd["attributes"] != {Attr.PURE}
            ]
            if not pure_with_el:
                pure_with_el = [i for i in PURE_ELEMENT_IDS if i in dragon_db]
            if pure_with_el:
                chosen = random.choice(pure_with_el)
                logger.info("Pure elemental dragon %s (%s)", chosen, dragon_db[chosen]["name"])
                return chosen

    if boosted:
        key = frozenset(pool)
        if key in LEGENDARY_COMBOS_BY_ATTRS:
            if random.uniform(0, 100) < LEGENDARY_FROM_COMBO_CHANCE:
                possible = [lid for lid in LEGENDARY_COMBOS_BY_ATTRS[key] if lid in dragon_db]
                if possible:
                    chosen = random.choice(possible)
                    logger.info("Legendary from combo: dragon %s (%s)", chosen, dragon_db[chosen]["name"])
                    return chosen

    candidates = []
    weights_diff = WEIGHT_DIFFICULTY_BOOSTED if boosted else WEIGHT_DIFFICULTY

    for dtype, ddata in dragon_db.items():
        if ddata["breedable"] == 0:
            continue
        if level1 < ddata["breedable"] or level2 < ddata["breedable"]:
            continue

        attrs = ddata["attributes"]
        if not attrs:
            continue
        if not attrs.issubset(pool):
            continue
        if Attr.LEGENDARY in attrs or Attr.PURE in attrs:
            continue

        diff = ddata["difficulty"]
        cat = ddata["category"]
        base_w = weights_diff.get(diff, 5)
        mult = CATEGORY_MULTIPLIER.get(cat, 0.01)
        final_w = base_w * mult

        if final_w > 0:
            candidates.append((dtype, final_w))

    if not candidates:
        logger.warning("No valid candidates by level/attributes, falling back to the first parent")
        return dragon1_type

    total = sum(w for _, w in candidates)
    r = random.uniform(0, total)
    cumulative = 0
    for dtype, w in candidates:
        cumulative += w
        if r <= cumulative:
            return dtype

    return candidates[-1][0]
