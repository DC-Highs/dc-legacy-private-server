"""Lookups in the game config item catalog."""
from typing import Any, Dict, Optional


def build_items_index(config: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    return {str(item.get("id")): item for item in config.get("items", [])}


def get_item_config(config: Dict[str, Any], model_id: Any) -> Optional[Dict[str, Any]]:
    model_id_str = str(model_id)
    for item in config.get("items", []):
        if str(item.get("id")) == model_id_str:
            return item
    return None
