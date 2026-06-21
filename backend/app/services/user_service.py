import re
from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload
from app.models.role import Role
from app.models.user import User

COMMON_PASSWORDS = {"admin123", "password", "12345678", "qwerty123"}
ROLE_PERMISSIONS = {
    "Admin": ["*"],
    "Manager": ["dashboards:read", "reports:read", "exports:run", "imports:preview", "imports:commit", "operations:manage"],
    "Data Entry Operator": ["dashboards:read", "reports:safe", "exports:safe", "imports:preview", "records:write"],
    "Viewer": ["dashboards:safe", "reports:safe", "exports:safe", "records:read"],
}

def validate_password(password: str, username: str, confirmation: str) -> None:
    errors=[]; lower=password.lower(); username_lower=username.lower()
    if password != confirmation: errors.append("Password and confirmation do not match")
    if len(password) < 8: errors.append("Password must contain at least 8 characters")
    if not re.search(r"[A-Z]", password): errors.append("Password must contain an uppercase letter")
    if not re.search(r"[a-z]", password): errors.append("Password must contain a lowercase letter")
    if not re.search(r"\d", password): errors.append("Password must contain a number")
    if not re.search(r"[^A-Za-z0-9]", password): errors.append("Password must contain a special character")
    if username_lower and username_lower in lower: errors.append("Password must not contain the username")
    if lower in COMMON_PASSWORDS: errors.append("Password is too common")
    if errors: raise HTTPException(422, "; ".join(errors))

def get_user_or_404(db: Session, user_id: int) -> User:
    user=db.scalar(select(User).options(selectinload(User.roles)).where(User.id==user_id))
    if user is None: raise HTTPException(404,"User not found")
    return user

def roles_or_422(db: Session, role_ids: list[int]) -> list[Role]:
    ids=set(role_ids); roles=list(db.scalars(select(Role).where(Role.id.in_(ids))).all()) if ids else []
    if len(roles) != len(ids): raise HTTPException(422,"One or more roles do not exist")
    return roles

def user_response(user: User):
    from app.schemas.users import UserAdminResponse
    return UserAdminResponse(id=user.id,username=user.username,email=user.email,full_name=user.full_name,is_active=user.is_active,force_password_change=user.force_password_change,roles=sorted(role.name for role in user.roles),created_at=user.created_at,updated_at=user.updated_at)

def effective_permissions(user: User) -> list[str]:
    values=set()
    for role in user.roles: values.update(ROLE_PERMISSIONS.get(role.name,[f"role:{role.name}"]))
    return sorted(values)

def ensure_not_last_admin(db: Session, user: User) -> None:
    if not user.is_active or "Admin" not in {role.name for role in user.roles}: return
    count=db.scalar(select(func.count(func.distinct(User.id))).select_from(User).join(User.roles).where(User.is_active.is_(True),Role.name=="Admin")) or 0
    if count <= 1: raise HTTPException(409,"The last active Admin user cannot be deactivated")
