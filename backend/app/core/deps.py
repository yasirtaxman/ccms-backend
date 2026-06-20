from collections.abc import Callable

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import SessionLocal
from app.models.role import Role
from app.models.user import User


def get_db():
    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id = payload.get("user_id")
        subject = payload.get("sub")
        if user_id is None or subject is None:
            raise credentials_error
        user_id = int(user_id)
    except (JWTError, TypeError, ValueError):
        raise credentials_error

    user = db.scalar(select(User).where(User.id == user_id, User.username == subject))
    if user is None:
        raise credentials_error
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is disabled")
    return user


ROLE_ADMIN = "Admin"
ROLE_MANAGER = "Manager"
ROLE_DATA_ENTRY = "Data Entry Operator"
ROLE_VIEWER = "Viewer"


def require_roles(*allowed_roles: str) -> Callable[..., User]:
    def role_dependency(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
    ) -> User:
        role_names = set(
            db.scalars(
                select(Role.name).join(Role.users).where(User.id == current_user.id)
            ).all()
        )
        if ROLE_ADMIN not in role_names and role_names.isdisjoint(allowed_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return current_user

    return role_dependency


require_admin = require_roles(ROLE_ADMIN)
require_manager = require_roles(ROLE_MANAGER)
require_data_entry = require_roles(ROLE_DATA_ENTRY)
require_viewer = require_roles(ROLE_VIEWER)

can_create_or_update = require_roles(ROLE_MANAGER, ROLE_DATA_ENTRY)
can_read = require_roles(ROLE_MANAGER, ROLE_VIEWER)
can_sponsor_read = require_roles(ROLE_MANAGER, ROLE_DATA_ENTRY, ROLE_VIEWER)
can_operational_read = require_roles(ROLE_MANAGER, ROLE_DATA_ENTRY, ROLE_VIEWER)
