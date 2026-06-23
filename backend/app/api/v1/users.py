from datetime import UTC, datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload
from app.core.deps import get_current_user, get_db, require_admin
from app.core.security import hash_password, verify_password
from app.models.user import User
from app.schemas.users import (ChangePasswordRequest, PasswordResetRequest, RoleAssignmentRequest,
    UserAdminCreate, UserAdminResponse, UserAdminUpdate, UserListResponse, UserPermissionsResponse)
from app.services.audit import AuditAction, AuditModule, add_audit_log
from app.services.user_service import (effective_permissions, ensure_not_last_admin, get_user_or_404,
    roles_or_422, user_response, validate_password)

router = APIRouter(tags=["Users"])

@router.get("/users", response_model=UserListResponse)
def list_users(limit:int=Query(50,ge=1,le=500),offset:int=Query(0,ge=0),db:Session=Depends(get_db),_:User=Depends(require_admin)):
    total=db.scalar(select(func.count()).select_from(User)) or 0
    users=db.scalars(select(User).options(selectinload(User.roles)).order_by(User.username).offset(offset).limit(limit)).all()
    return UserListResponse(data=[user_response(u) for u in users],limit=limit,offset=offset,total=total)

@router.get("/users/me/permissions", response_model=UserPermissionsResponse)
def permissions(user:User=Depends(get_current_user)):
    return UserPermissionsResponse(user_id=user.id,username=user.username,roles=sorted(r.name for r in user.roles),effective_permissions=effective_permissions(user))

@router.get("/users/{user_id}", response_model=UserAdminResponse)
def get_user(user_id:int,db:Session=Depends(get_db),_:User=Depends(require_admin)): return user_response(get_user_or_404(db,user_id))

@router.post("/users", response_model=UserAdminResponse, status_code=status.HTTP_201_CREATED)
def create_user(payload:UserAdminCreate,db:Session=Depends(get_db),admin:User=Depends(require_admin)):
    validate_password(payload.password,payload.username,payload.confirm_password)
    duplicate=User.username==payload.username
    if payload.email is not None: duplicate=or_(duplicate,User.email==payload.email)
    if db.scalar(select(User).where(duplicate)): raise HTTPException(409,"Username or email already exists")
    roles=roles_or_422(db,payload.role_ids)
    user=User(username=payload.username,email=payload.email,full_name=payload.full_name,password_hash=hash_password(payload.password),is_active=payload.is_active,force_password_change=False,roles=roles)
    db.add(user)
    try:
        db.flush(); add_audit_log(db,user_id=admin.id,action=AuditAction.USER_CREATE,module=AuditModule.USER_ADMINISTRATION,record_id=user.id,new_values={"username":user.username,"email":user.email,"is_active":user.is_active,"roles":[r.name for r in roles]}); db.commit()
    except IntegrityError: db.rollback(); raise HTTPException(409,"Username or email already exists")
    return user_response(user)

@router.put("/users/{user_id}", response_model=UserAdminResponse)
def update_user(user_id:int,payload:UserAdminUpdate,db:Session=Depends(get_db),admin:User=Depends(require_admin)):
    user=get_user_or_404(db,user_id); changes=payload.model_dump(exclude_unset=True); old={key:getattr(user,key) for key in changes}
    if changes.get("is_active") is False: ensure_not_last_admin(db,user)
    for key,value in changes.items(): setattr(user,key,value)
    user.updated_at=datetime.now(UTC); add_audit_log(db,user_id=admin.id,action=AuditAction.USER_UPDATE,module=AuditModule.USER_ADMINISTRATION,record_id=user.id,old_values=old,new_values=changes)
    try: db.commit()
    except IntegrityError: db.rollback(); raise HTTPException(409,"Email already exists")
    return user_response(user)

@router.post("/users/{user_id}/roles", response_model=UserAdminResponse)
def replace_roles(user_id:int,payload:RoleAssignmentRequest,db:Session=Depends(get_db),admin:User=Depends(require_admin)):
    user=get_user_or_404(db,user_id); roles=roles_or_422(db,payload.role_ids); old=sorted(r.name for r in user.roles)
    if "Admin" in old and "Admin" not in {r.name for r in roles}: ensure_not_last_admin(db,user)
    user.roles=roles; add_audit_log(db,user_id=admin.id,action=AuditAction.USER_ROLE_ASSIGN,module=AuditModule.USER_ADMINISTRATION,record_id=user.id,old_values={"roles":old},new_values={"roles":sorted(r.name for r in roles)}); db.commit(); return user_response(user)

def set_active(db,user,admin,active):
    if not active: ensure_not_last_admin(db,user)
    old=user.is_active; user.is_active=active; user.updated_at=datetime.now(UTC)
    action=AuditAction.USER_ACTIVATE if active else AuditAction.USER_DEACTIVATE
    add_audit_log(db,user_id=admin.id,action=action,module=AuditModule.USER_ADMINISTRATION,record_id=user.id,old_values={"is_active":old},new_values={"is_active":active}); db.commit(); return user_response(user)

@router.post("/users/{user_id}/activate", response_model=UserAdminResponse)
def activate(user_id:int,db:Session=Depends(get_db),admin:User=Depends(require_admin)): return set_active(db,get_user_or_404(db,user_id),admin,True)

@router.post("/users/{user_id}/deactivate", response_model=UserAdminResponse)
def deactivate(user_id:int,db:Session=Depends(get_db),admin:User=Depends(require_admin)): return set_active(db,get_user_or_404(db,user_id),admin,False)

@router.post("/users/{user_id}/reset-password", response_model=UserAdminResponse)
def reset_password(user_id:int,payload:PasswordResetRequest,db:Session=Depends(get_db),admin:User=Depends(require_admin)):
    user=get_user_or_404(db,user_id); validate_password(payload.new_password,user.username,payload.confirm_password)
    user.password_hash=hash_password(payload.new_password); user.force_password_change=payload.force_password_change; user.updated_at=datetime.now(UTC)
    add_audit_log(db,user_id=admin.id,action=AuditAction.USER_PASSWORD_RESET,module=AuditModule.USER_ADMINISTRATION,record_id=user.id,new_values={"force_password_change":payload.force_password_change}); db.commit(); return user_response(user)

@router.post("/auth/change-password")
def change_password(payload:ChangePasswordRequest,db:Session=Depends(get_db),user:User=Depends(get_current_user)):
    if not verify_password(payload.current_password,user.password_hash): raise HTTPException(400,"Current password is incorrect")
    validate_password(payload.new_password,user.username,payload.confirm_password)
    user.password_hash=hash_password(payload.new_password); user.force_password_change=False; user.updated_at=datetime.now(UTC)
    add_audit_log(db,user_id=user.id,action=AuditAction.USER_PASSWORD_CHANGE,module=AuditModule.USER_ADMINISTRATION,record_id=user.id,new_values={"password_changed":True}); db.commit(); return {"message":"Password changed successfully"}
