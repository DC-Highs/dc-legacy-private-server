"""Enumerations for the wire protocol and the game data the server understands.

Every enum that crosses the network (commands, SSE events, endpoint names) keeps
the exact string the Flash client sends or expects as its value.
"""
from enum import Enum, IntEnum


class Command(str, Enum):
    """Commands the client batches inside a ``packet.php`` request."""

    BUY = "buy"
    BUY_EGG = "buy_egg"
    HATCH_EGG = "hatch_egg"
    MISTERY_EGG_HATCH = "mistery_egg_hatch"
    FEED_DRAGON = "feed_dragon"
    SET_GOALS = "set_goals"
    COMPLETE_GOAL = "complete_goal"
    BREED_DRAGON = "breed_dragon"
    MOVE = "move"
    STORE_ITEM = "store_item"
    PLACE_STORED_EGG = "place_stored_egg"
    PLACE_STORED_DRAGON = "place_stored_dragon"
    DRAGONARIUM_PLACE_STORED = "dragonarium_place_stored"
    SELL = "sell"
    SELL_EGG = "sell_egg"
    SELL_DRAGON = "sell_dragon"
    SELL_STORED_ITEM = "sell_stored_item"
    SELL_STORED_DRAGON = "sell_stored_dragon"
    ORIENT = "orient"
    LEVEL_UP = "level_up"
    COMPLETE_TUTORIAL = "complete_tutorial"
    COLLECT = "collect"
    EXPAND_GOLD = "expand_gold"
    EXPAND_CASH = "expand_cash"
    ACTIVATE = "activate"
    FINISH_BUILDING = "finish_building"
    UPGRADE = "upgrade"
    RENAME_DRAGON = "rename_dragon"
    SPEED_COLLECT = "speed_collect"
    SPEED_HATCH = "speed_hatch"
    SYNC = "sync"
    PING = "ping"
    FINISH_BREEDING2 = "finish_breeding2"
    EXPAND_ISLAND = "expand_island"
    MOVE_DRAGON = "move_dragon"
    BUY_TREASURE_NEW = "buy_treasure_new"
    SET_ATTACK_TEAM = "set_attack_team"
    DEUS_CARDS_GENERATE = "deus_cards_generate"
    DEUS_CARDS_CLAIM = "deus_cards_claim"
    BEGIN_TOURNAMENT = "begin_tournament"
    END_TOURNAMENT = "end_tournament"
    ADMIN_SPEED_TOURNAMENT = "admin_speed_tournament"
    START_TRAINING = "start_training"
    SPEED_TRAINING = "speed_training"
    FINISH_TRAINING = "finish_training"
    WEEKLY_REWARD = "weekly_reward"
    PLACE_STORED_ITEM = "place_stored_item"
    BUY_TREASURE_POPUP = "buy_treasure_popup"
    COMPLETE_COLLECTION = "complete_collection"
    DRAGONARIUM_PUSH = "dragonarium_push"
    DRAGONARIUM_PULL = "dragonarium_pull"
    DRAGONARIUM_ADD = "dragonarium_add"
    SET_HELP_MAP = "set_help_map"
    ATTACK_PLAYER = "attack_player"
    END_ATTACK_F = "end_attack_f"
    ASSIST_NEIGHBOR = "assist_neighbor"
    CLEAN_RECEIVED_ASSISTS = "clean_received_assists"
    ASSIST_RECEIVE = "assist_receive"
    KOMPU_BOXES_NEW_LIST = "kompu_boxes_new_list"
    KOMPU_BOXES_OPEN_BOX = "kompu_boxes_open_box"
    KOMPU_BOXES_CLAIM_PRIZE = "kompu_boxes_claim_prize"


class SseEvent(str, Enum):
    """Messages pushed to the client through the ``/stream`` channel."""

    # The client compares against this literal in templates/index.html.
    GAME_SAVED = "JUEGO_GUARDADO"
    PING = "PING"


class SrvEndpoint(str, Enum):
    """File names served by ``/static/dragoncity/srv/<filename>``."""

    GAME_CONFIG_JSON = "get_game_config.json"
    GAME_CONFIG_PHP = "get_game_config.php"
    PVP_ISLE_JSON = "get_pvp_isle.json"
    PVP_ISLE_PHP = "get_pvp_isle.php"
    PVP_ISLE_INFO_PHP = "get_pvp_isle_info.php"
    PLAYER_INFO_JSON = "get_player_info.json"
    PLAYER_INFO_PHP = "get_player_info.php"


class Resource(str, Enum):
    """Keys of the player's ``playerInfo`` resource counters."""

    GOLD = "gold"
    CASH = "cash"
    FOOD = "food"
    XP = "xp"


class GroupType(str, Enum):
    """``group_type`` values found in the game config items."""

    DRAGON = "DRAGON"
    HABITAT = "HABITAT"
    FARM = "FARM"
    OBSTACLE = "OBSTACLE"


class DragonAttribute(str, Enum):
    """Element and rarity attribute codes of a dragon."""

    EARTH = "e"
    FIRE = "f"
    WATER = "w"
    PLANT = "p"
    ELECTRIC = "el"
    METAL = "m"
    DARK = "d"
    LIGHT = "li"
    ICE = "i"
    WAR = "wr"
    PURE = "pu"
    LEGENDARY = "l"


class DragonariumTab(IntEnum):
    """Tabs (and slot categories) of the dragonarium."""

    ELEMENTAL = 0
    METAL = 1
    DARK = 2
    LEGENDARY = 3
    PURE = 4


class OfferType(str, Enum):
    """Kinds of offers sold in the achievement-points market."""

    GOLD = "gold"
    FOOD = "food"
    GEMS = "gems"
    DRAGON = "dragon"
