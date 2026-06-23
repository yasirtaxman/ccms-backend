from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.deps import get_db, require_admin
from app.models.role import Role, UserRole
from app.models.permission import Permission
from app.models.user import User
from app.schemas.role import PermissionResponse,RoleAssignmentResponse,RoleCreate,RolePermissionsUpdate,RoleResponse,RoleUpdate
from app.schemas.users import RoleAssignmentRequest
from app.services.permission_service import seed_permissions
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

    role = Role(name=payload.name,is_system=False)
    db.add(role)
    try:
        db.flush()
        add_audit_log(
            db,
            user_id=current_user.id,
            action=AuditAction.ROLE_CREATED,
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
    seed_permissions(db);db.commit();return db.scalars(select(Role).order_by(Role.name)).all()

@router.get("/permissions",response_model=list[PermissionResponse])
def list_permissions(db:Session=Depends(get_db),_:User=Depends(require_admin)):
    seed_permissions(db);db.commit();return db.scalars(select(Permission).order_by(Permission.module,Permission.action)).all()

@router.get("/roles/{role_id}",response_model=RoleResponse)
def get_role(role_id:int,db:Session=Depends(get_db),_:User=Depends(require_admin)):
    role=db.get(Role,role_id)
    if not role:raise HTTPException(404,"Role not found")
    return role

@router.put("/roles/{role_id}",response_model=RoleResponse)
def update_role(role_id:int,payload:RoleUpdate,db:Session=Depends(get_db),user:User=Depends(require_admin)):
    role=db.get(Role,role_id)
    if not role:raise HTTPException(404,"Role not found")
    if role.name=="Admin":raise HTTPException(409,"Admin role name is protected")
    old=role.name;role.name=payload.name;add_audit_log(db,user_id=user.id,action=AuditAction.ROLE_UPDATED,module=AuditModule.ROLES,record_id=role.id,old_values={"name":old},new_values={"name":role.name});db.commit();return role

@router.delete("/roles/{role_id}")
def delete_role(role_id:int,db:Session=Depends(get_db),user:User=Depends(require_admin)):
    role=db.get(Role,role_id)
    if not role:raise HTTPException(404,"Role not found")
    if role.is_system or role.name in {"Admin","Manager","Data Entry Operator","Viewer","Warden"}:raise HTTPException(409,"System roles cannot be deleted")
    if db.scalar(select(UserRole.id).where(UserRole.role_id==role.id).limit(1)):raise HTTPException(409,"Role is assigned to users")
    old={"name":role.name};db.delete(role);add_audit_log(db,user_id=user.id,action=AuditAction.ROLE_DELETED,module=AuditModule.ROLES,record_id=role_id,old_values=old);db.commit();return {"message":"Role deleted"}

@router.get("/roles/{role_id}/permissions",response_model=list[PermissionResponse])
def role_permissions(role_id:int,db:Session=Depends(get_db),_:User=Depends(require_admin)):
    seed_permissions(db);role=db.get(Role,role_id)
    if not role:raise HTTPException(404,"Role not found")
    db.commit();return sorted(role.permissions,key=lambda item:item.name)

@router.put("/roles/{role_id}/permissions",response_model=list[PermissionResponse])
def replace_permissions(role_id:int,payload:RolePermissionsUpdate,db:Session=Depends(get_db),user:User=Depends(require_admin)):
    seed_permissions(db);role=db.get(Role,role_id)
    if not role:raise HTTPException(404,"Role not found")
    if role.name=="Admin":raise HTTPException(409,"Admin permissions are protected")
    permissions=list(db.scalars(select(Permission).where(Permission.id.in_(set(payload.permission_ids)))).all()) if payload.permission_ids else []
    if len(permissions)!=len(set(payload.permission_ids)):raise HTTPException(422,"Unknown permission ID")
    old={"permissions":sorted(item.name for item in role.permissions)};role.permissions=permissions;role.permissions_configured=True;add_audit_log(db,user_id=user.id,action=AuditAction.ROLE_PERMISSIONS_UPDATED,module=AuditModule.ROLES,record_id=role.id,old_values=old,new_values={"permissions":sorted(item.name for item in permissions)});db.commit();return sorted(role.permissions,key=lambda item:item.name)

@router.post("/roles/{role_id}/permissions",response_model=list[PermissionResponse])
def add_permissions(role_id:int,payload:RolePermissionsUpdate,db:Session=Depends(get_db),user:User=Depends(require_admin)):
    role=db.get(Role,role_id)
    if not role:raise HTTPException(404,"Role not found")
    return replace_permissions(role_id,RolePermissionsUpdate(permission_ids=sorted({item.id for item in role.permissions}|set(payload.permission_ids))),db,user)

@router.delete("/roles/{role_id}/permissions/{permission_id}")
def remove_permission(role_id:int,permission_id:int,db:Session=Depends(get_db),user:User=Depends(require_admin)):
    role=db.get(Role,role_id)
    if not role:raise HTTPException(404,"Role not found")
    if role.name=="Admin":raise HTTPException(409,"Admin permissions are protected")
    return replace_permissions(role_id,RolePermissionsUpdate(permission_ids=[item.id for item in role.permissions if item.id!=permission_id]),db,user)


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

@router.put("/users/{user_id}/roles",response_model=list[RoleResponse])
def replace_user_roles(user_id:int,payload:RoleAssignmentRequest,db:Session=Depends(get_db),admin:User=Depends(require_admin)):
    user=db.get(User,user_id)
    if not user:raise HTTPException(404,"User not found")
    roles=list(db.scalars(select(Role).where(Role.id.in_(set(payload.role_ids)))).all()) if payload.role_ids else []
    if len(roles)!=len(set(payload.role_ids)):raise HTTPException(422,"Unknown role ID")
    if "Admin" in {role.name for role in user.roles} and "Admin" not in {role.name for role in roles}:
        from app.services.user_service import ensure_not_last_admin
        ensure_not_last_admin(db,user)
    old=sorted(role.name for role in user.roles);user.roles=roles;add_audit_log(db,user_id=admin.id,action=AuditAction.USER_ROLES_UPDATED,module=AuditModule.ROLES,record_id=user.id,old_values={"roles":old},new_values={"roles":sorted(role.name for role in roles)});db.commit();return roles
