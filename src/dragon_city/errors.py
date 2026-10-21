"""Errors that are turned into JSON responses by the API layer."""
from typing import Dict, Optional


class ApiError(Exception):
    def __init__(self, status: int, code: str, message: str, fields: Optional[Dict[str, str]] = None):
        super().__init__(message)
        self.status = status
        self.code = code
        self.message = message
        self.fields = fields or {}

    def to_dict(self) -> Dict[str, object]:
        body: Dict[str, object] = {"code": self.code, "message": self.message}
        if self.fields:
            body["fields"] = self.fields
        return {"error": body}


def validation_error(fields: Dict[str, str]) -> ApiError:
    return ApiError(400, "validation_error", "Some fields are invalid", fields)


def unauthorized(message: str = "Authentication required") -> ApiError:
    return ApiError(401, "unauthorized", message)


def forbidden(message: str = "You are not allowed to do this") -> ApiError:
    return ApiError(403, "forbidden", message)


def not_found(message: str = "Not found") -> ApiError:
    return ApiError(404, "not_found", message)


def conflict(message: str, fields: Optional[Dict[str, str]] = None) -> ApiError:
    return ApiError(409, "conflict", message, fields)
