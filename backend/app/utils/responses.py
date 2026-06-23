from typing import Any
from app.schemas.common import APIResponse, ErrorItem

def success_response(message: str, data: Any = None, meta: dict | None = None) -> dict:
    return APIResponse(success=True, message=message, data=data, errors=None, meta=meta or {}).model_dump()

def error_response(message: str, errors: list[dict] | None = None, meta: dict | None = None) -> dict:
    items = [ErrorItem(**item) for item in (errors or [{"message": message, "code": "error"}])]
    return APIResponse(success=False, message=message, data=None, errors=items, meta=meta or {}).model_dump()
