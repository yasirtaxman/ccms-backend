from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.models.child import Child
from app.schemas.child import ChildCreate, ChildUpdate
from app.core.deps import get_db

router = APIRouter()


@router.post("/children")
def create_child(
    child: ChildCreate,
    db: Session = Depends(get_db)
):
    db_child = Child(**child.model_dump())

    db.add(db_child)
    db.commit()
    db.refresh(db_child)

    return db_child


@router.get("/children")
def get_children(
    db: Session = Depends(get_db)
):
    children = db.query(Child).all()

    return children


@router.get("/children/{child_id}")
def get_child(
    child_id: int,
    db: Session = Depends(get_db)
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
    db: Session = Depends(get_db)
):
    child = db.query(Child).filter(
        Child.id == child_id
    ).first()

    if not child:
        raise HTTPException(
            status_code=404,
            detail="Child not found"
        )

    for key, value in child_data.model_dump().items():
        setattr(child, key, value)

    db.commit()
    db.refresh(child)

    return child