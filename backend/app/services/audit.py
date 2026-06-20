from enum import Enum
from typing import Any

from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog


class AuditAction(str, Enum):
    CREATE = "CREATE"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    VERIFY = "VERIFY"
    LOGIN = "LOGIN"
    SPONSORSHIP_STATUS_CHANGE = "SPONSORSHIP_STATUS_CHANGE"
    BED_ALLOCATION = "BED_ALLOCATION"
    BED_TRANSFER = "BED_TRANSFER"
    BED_VACATION = "BED_VACATION"


class AuditModule(str, Enum):
    AUTH = "AUTH"
    CHILDREN = "CHILDREN"
    DOCUMENTS = "DOCUMENTS"
    USERS = "USERS"
    ROLES = "ROLES"
    SPONSORS = "SPONSORS"
    SPONSORSHIPS = "SPONSORSHIPS"
    ACCOMMODATION = "ACCOMMODATION"
    BED_ALLOCATIONS = "BED_ALLOCATIONS"


def add_audit_log(
    db: Session,
    *,
    user_id: int | None,
    action: AuditAction,
    module: AuditModule,
    record_id: int | None = None,
    old_values: dict[str, Any] | None = None,
    new_values: dict[str, Any] | None = None,
) -> AuditLog:
    log = AuditLog(
        user_id=user_id,
        action=action.value,
        module=module.value,
        record_id=record_id,
        old_values=jsonable_encoder(old_values) if old_values is not None else None,
        new_values=jsonable_encoder(new_values) if new_values is not None else None,
    )
    db.add(log)
    return log
