from typing import Any

from pydantic import BaseModel, ConfigDict


class ImportValidationError(BaseModel):
    row: int
    field: str | None = None
    message: str
    model_config = ConfigDict(extra="forbid")


class ImportPreviewResponse(BaseModel):
    total_rows: int
    valid_rows: int
    invalid_rows: int
    duplicate_rows: int
    validation_errors: list[ImportValidationError]
    preview_data: list[dict[str, Any]]
    model_config = ConfigDict(extra="forbid")


class ImportCommitResponse(BaseModel):
    imported_count: int
    skipped_count: int
    errors: list[ImportValidationError]
    created_child_ids: list[int]
    model_config = ConfigDict(extra="forbid")


class ExportRequestInfo(BaseModel):
    report_type: str
    generated_by: str
    filters_applied: dict[str, Any]
    model_config = ConfigDict(extra="forbid")
