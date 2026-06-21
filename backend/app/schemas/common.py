from typing import Any
from pydantic import BaseModel, ConfigDict, Field

class ErrorItem(BaseModel):
    field: str | None = None
    message: str
    code: str
    model_config = ConfigDict(extra="forbid")

class APIResponse(BaseModel):
    success: bool
    message: str
    data: Any | None = None
    errors: list[ErrorItem] | None = None
    meta: dict[str, Any] = Field(default_factory=dict)
    model_config = ConfigDict(extra="forbid")
