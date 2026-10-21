"""JSON API used by the web client and the admin panel."""
from typing import Any, Dict, Type, TypeVar

from flask import request
from pydantic import BaseModel
from pydantic import ValidationError as PydanticValidationError

from dragon_city.errors import validation_error

M = TypeVar("M", bound=BaseModel)


def parse_body(model: Type[M]) -> M:
    """Validate the JSON body against ``model``; failures become a field-level 400."""
    data: Any = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise validation_error({"_": "A JSON object body is required"})
    try:
        return model.model_validate(data)
    except PydanticValidationError as exc:
        fields: Dict[str, str] = {}
        for item in exc.errors():
            name = ".".join(str(part) for part in item["loc"]) or "_"
            fields.setdefault(name, item["msg"])
        raise validation_error(fields)
