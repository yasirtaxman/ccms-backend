from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.deps import get_db, require_admin
from app.models.role import Role, UserRole
from app.models.user import User
from app.schemas.role import RoleAssignmentResponse, RoleCreate, RoleResponse
from app.services.audit import AuditAction, AuditModule, add_audit_log

router = APIRouter(tags=["Roles"])


@router.post("/roles", response_model=RoleResponse, status_code=status.HTTP_201_CREATED)
def create_role(
    payload: RoleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    existing = db.scalar(select(Role).where(Role.name.ilike(payload.name)))
    if existing:
        raise HTTPException(status_code=409, detail="Role already exists")

    role = Role(name=payload.name)
    db.add(role)
    try:
        db.flush()
        add_audit_log(
            db,
            user_id=current_user.id,
            action=AuditAction.CREATE,
            module=AuditModule.ROLES,
            record_id=role.id,
            new_values={"name": role.name},
        )
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Role already exists")
    db.refresh(role)
    return role


@router.get("/roles", response_model=list[RoleResponse])
def list_roles(
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_admin),
):
    return db.scalars(select(Role).order_by(Role.name)).all()


@router.post(
    "/users/{user_id}/roles/{role_id}",
    response_model=RoleAssignmentResponse,
    status_code=status.HTTP_201_CREATED,
)
def assign_role(
    user_id: int,
    role_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    role = db.get(Role, role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    if db.scalar(
        select(UserRole).where(UserRole.user_id == user_id, UserRole.role_id == role_id)
    ):
        raise HTTPException(status_code=409, detail="Role is already assigned to user")

    db.add(UserRole(user_id=user_id, role_id=role_id))
    add_audit_log(
        db,
        user_id=current_user.id,
        action=AuditAction.UPDATE,
        module=AuditModule.ROLES,
        record_id=role_id,
        new_values={"assigned_to_user_id": user_id, "role_name": role.name},
    )
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Role is already assigned to user")
    return RoleAssignmentResponse(
        user_id=user_id, role=role, message="Role assigned successfully"
    )


@router.get("/users/{user_id}/roles", response_model=list[RoleResponse])
def list_user_roles(
    user_id: int,
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_admin),
):
    if not db.get(User, user_id):
        raise HTTPException(status_code=404, detail="User not found")
    return db.scalars(
        select(Role).join(Role.users).where(User.id == user_id).order_by(Role.name)
    ).all()
