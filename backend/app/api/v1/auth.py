from datetime import UTC, datetime
from sqlalchemy.orm import Session
from sqlalchemy import or_

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.core.deps import get_current_user, get_db
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token
)

from app.models.user import User

from app.schemas.user import (
    UserCreate,
    UserLogin,
    UserResponse,
    CurrentUser,
    Token,
)
from app.services.audit import AuditAction, AuditModule, add_audit_log
from app.services.user_service import validate_password

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)


@router.post(
    "/register",
    response_model=UserResponse
)
def register_user(
    user: UserCreate,
    db: Session = Depends(get_db)
):
    validate_password(user.password, user.username, user.password)
    existing_user = db.query(User).filter(
        or_(
            User.username == user.username,
            User.email == user.email
        )
    ).first()

    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Username or Email already exists"
        )

    db_user = User(
        full_name=user.full_name,
        username=user.username,
        email=user.email,
        password_hash=hash_password(
            user.password
        ),
        is_active=True
    )

    db.add(db_user)
    db.flush()
    add_audit_log(
        db,
        user_id=db_user.id,
        action=AuditAction.CREATE,
        module=AuditModule.USERS,
        record_id=db_user.id,
        new_values={
            "full_name": db_user.full_name,
            "username": db_user.username,
            "email": db_user.email,
            "is_active": db_user.is_active,
        },
    )
    db.commit()
    db.refresh(db_user)

    return db_user


@router.post(
    "/login",
    response_model=Token
)
def login(
    login_data: UserLogin,
    db: Session = Depends(get_db)
):
    return _authenticate(login_data.username_or_email, login_data.password, db)


@router.post(
    "/token",
    response_model=Token,
    summary="OAuth2-compatible login for Swagger UI",
)
def oauth2_login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    return _authenticate(form_data.username, form_data.password, db)


@router.get("/me", response_model=CurrentUser)
def read_current_user(current_user: User = Depends(get_current_user)):
    return CurrentUser(
        id=current_user.id,
        full_name=current_user.full_name,
        username=current_user.username,
        email=current_user.email,
        is_active=current_user.is_active,
        roles=[role.name for role in current_user.roles],
    )


def _authenticate(username_or_email: str, password: str, db: Session) -> dict[str, str]:
    user = db.query(User).filter(
        or_(
            User.username == username_or_email,
            User.email == username_or_email,
        )
    ).first()

    if not user:
        add_audit_log(db, user_id=None, action=AuditAction.USER_LOGIN_FAILED,
                      module=AuditModule.USER_ADMINISTRATION,
                      new_values={"login_identifier": username_or_email[:100]})
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    if not verify_password(
        password,
        user.password_hash
    ):
        add_audit_log(db, user_id=user.id, action=AuditAction.USER_LOGIN_FAILED,
                      module=AuditModule.USER_ADMINISTRATION, record_id=user.id,
                      new_values={"username": user.username})
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    if not user.is_active:
        add_audit_log(db, user_id=user.id, action=AuditAction.USER_LOGIN_FAILED,
                      module=AuditModule.USER_ADMINISTRATION, record_id=user.id,
                      new_values={"username": user.username, "reason": "inactive"})
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid credentials",
        )

    access_token = create_access_token(
        {
            "sub": user.username,
            "user_id": user.id
        }
    )

    add_audit_log(
        db,
        user_id=user.id,
        action=AuditAction.LOGIN,
        module=AuditModule.AUTH,
        record_id=user.id,
        new_values={"username": user.username},
    )
    user.last_login_at = datetime.now(UTC)
    add_audit_log(db, user_id=user.id, action=AuditAction.USER_LOGIN_SUCCESS,
                  module=AuditModule.USER_ADMINISTRATION, record_id=user.id,
                  new_values={"username": user.username})
    db.commit()

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }
