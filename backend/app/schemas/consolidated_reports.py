from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class PaginationInfo(BaseModel):
    limit: int
    offset: int
    total: int
    model_config = ConfigDict(extra="forbid")


class ConsolidatedReportResponse(BaseModel):
    data: list[dict[str, Any]]
    pagination: PaginationInfo
    filters_applied: dict[str, Any]
    generated_at: datetime
    generated_by: str
    export_ready: bool = True
    model_config = ConfigDict(extra="forbid")


class AuditRanking(BaseModel):
    key: str
    count: int
    model_config = ConfigDict(extra="forbid")


class AuditSummaryResponse(BaseModel):
    total_audit_logs: int
    logs_today: int
    logs_this_month: int
    top_actions: list[AuditRanking]
    top_modules: list[AuditRanking]
    top_users_by_activity: list[AuditRanking]
    model_config = ConfigDict(extra="forbid")
