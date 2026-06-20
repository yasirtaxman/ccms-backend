from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.models.child import Child
from app.schemas.child import ChildCreate, ChildUpdate
from app.core.deps import can_create_or_update, can_read, get_db
from app.models.user import User
from app.services.audit import AuditAction, AuditModule, add_audit_log

router = APIRouter()


@router.post("/children")
def create_child(
    child: ChildCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(can_create_or_update),
):
    db_child = Child(**child.model_dump())

    db.add(db_child)
    db.flush()
    add_audit_log(
        db,
        user_id=current_user.id,
        action=AuditAction.CREATE,
        module=AuditModule.CHILDREN,
        record_id=db_child.id,
        new_values=child.model_dump(),
    )
    db.commit()
    db.refresh(db_child)

    return db_child


@router.get("/children")
def get_children(
    db: Session = Depends(get_db),
    _current_user: User = Depends(can_read),
):
    children = db.query(Child).all()

    return children


@router.get("/children/{child_id}")
def get_child(
    child_id: int,
    db: Session = Depends(get_db),
    _current_user: User = Depends(can_read),
):
    child = db.query(Child).filter(
        Child.id == child_id
    ).first()

    if not child:
        raise HTTPException(
            status_code=404,
            detail="Child not found"
        )

    return child


@router.put("/children/{child_id}")
def update_child(
    child_id: int,
    child_data: ChildUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(can_create_or_update),
):
    child = db.query(Child).filter(
        Child.id == child_id
    ).first()

    if not child:
        raise HTTPException(
            status_code=404,
            detail="Child not found"
        )

    changes = child_data.model_dump()
    old_values = {key: getattr(child, key) for key in changes}

    for key, value in changes.items():
        setattr(child, key, value)

    add_audit_log(
        db,
        user_id=current_user.id,
        action=AuditAction.UPDATE,
        module=AuditModule.CHILDREN,
        record_id=child.id,
        old_values=old_values,
        new_values=changes,
    )
    db.commit()
    db.refresh(child)

    return child
