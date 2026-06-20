from datetime import UTC, date, datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.encoders import jsonable_encoder
from sqlalchemy import case, func, not_, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.inspection import inspect
from sqlalchemy.orm import Session

from app.core.deps import can_create_or_update, can_operational_read, get_db, require_admin
from app.models.accommodation import Bed, BedAllocation, Block, Building, Floor, Room
from app.models.child import Child
from app.models.user import User
from app.schemas.accommodation import (
    AccommodationDashboard,
    BedAllocationCreate,
    BedAllocationResponse,
    BedAllocationUpdate,
    BedCreate,
    BedResponse,
    BedTransferRequest,
    BedTransferResponse,
    BedUpdate,
    BedVacationRequest,
    BlockCreate,
    BlockResponse,
    BlockUpdate,
    BuildingCreate,
    BuildingResponse,
    BuildingUpdate,
    ChildWithoutBedResponse,
    FloorCreate,
    FloorResponse,
    FloorUpdate,
    OccupancyResponse,
    RoomCreate,
    RoomResponse,
    RoomUpdate,
)
from app.services.audit import AuditAction, AuditModule, add_audit_log

router = APIRouter(tags=["Accommodation"])


def snapshot(instance: Any) -> dict[str, Any]:
    return jsonable_encoder(
        {column.key: getattr(instance, column.key) for column in inspect(instance).mapper.column_attrs}
    )


def active_or_404(db: Session, model, record_id: int, label: str, *, lock: bool = False):
    statement = select(model).where(model.id == record_id, model.deleted_at.is_(None))
    if lock:
        statement = statement.with_for_update()
    record = db.scalar(statement)
    if record is None:
        raise HTTPException(status_code=404, detail=f"{label} not found")
    return record


def normalize_code(value: str) -> str:
    return value.strip().upper()


def audit_change(
    db: Session,
    user: User,
    action: AuditAction,
    record: Any,
    *,
    old_values: dict | None = None,
    new_values: dict | None = None,
) -> None:
    add_audit_log(
        db,
        user_id=user.id,
        action=action,
        module=AuditModule.ACCOMMODATION,
        record_id=record.id,
        old_values=old_values,
        new_values={"entity": record.__class__.__name__, **(new_values or {})},
    )


def commit_or_conflict(db: Session, detail: str) -> None:
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail=detail) from exc


def update_record(db: Session, record: Any, changes: dict, user: User) -> Any:
    if not changes:
        return record
    old_values = {key: getattr(record, key) for key in changes}
    for key, value in changes.items():
        setattr(record, key, value)
    record.updated_by = user.id
    audit_change(db, user, AuditAction.UPDATE, record, old_values=old_values, new_values=changes)
    commit_or_conflict(db, f"Duplicate or invalid {record.__class__.__name__.lower()} data")
    db.refresh(record)
    return record


def soft_delete(db: Session, record: Any, user: User) -> Any:
    old_values = snapshot(record)
    record.deleted_at = datetime.now(UTC)
    record.deleted_by = user.id
    record.updated_by = user.id
    audit_change(
        db,
        user,
        AuditAction.DELETE,
        record,
        old_values=old_values,
        new_values={"deleted_at": record.deleted_at, "deleted_by": user.id},
    )
    db.commit()
    db.refresh(record)
    return record


def pagination(statement, skip: int, limit: int):
    return statement.offset(skip).limit(limit)


@router.post("/buildings", response_model=BuildingResponse, status_code=201)
def create_building(payload: BuildingCreate, db: Session = Depends(get_db), user: User = Depends(can_create_or_update)):
    values = payload.model_dump(mode="json")
    values["building_code"] = normalize_code(values["building_code"])
    record = Building(**values, created_by=user.id, updated_by=user.id)
    db.add(record)
    try:
        db.flush()
        audit_change(db, user, AuditAction.CREATE, record, new_values=snapshot(record))
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Building code already exists") from exc
    db.refresh(record)
    return record


@router.get("/buildings", response_model=list[BuildingResponse])
def list_buildings(skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=500), db: Session = Depends(get_db), _user: User = Depends(can_operational_read)):
    return db.scalars(pagination(select(Building).where(Building.deleted_at.is_(None)).order_by(Building.building_code), skip, limit)).all()


@router.get("/buildings/{record_id}", response_model=BuildingResponse)
def get_building(record_id: int, db: Session = Depends(get_db), _user: User = Depends(can_operational_read)):
    return active_or_404(db, Building, record_id, "Building")


@router.put("/buildings/{record_id}", response_model=BuildingResponse)
def update_building(record_id: int, payload: BuildingUpdate, db: Session = Depends(get_db), user: User = Depends(can_create_or_update)):
    changes = payload.model_dump(exclude_unset=True, mode="json")
    if changes.get("building_code"):
        changes["building_code"] = normalize_code(changes["building_code"])
    return update_record(db, active_or_404(db, Building, record_id, "Building"), changes, user)


@router.delete("/buildings/{record_id}", response_model=BuildingResponse)
def delete_building(record_id: int, db: Session = Depends(get_db), user: User = Depends(require_admin)):
    record = active_or_404(db, Building, record_id, "Building")
    if db.scalar(select(Block.id).where(Block.building_id == record.id).limit(1)):
        raise HTTPException(status_code=409, detail="Cannot delete building while blocks exist")
    return soft_delete(db, record, user)


@router.post("/blocks", response_model=BlockResponse, status_code=201)
def create_block(payload: BlockCreate, db: Session = Depends(get_db), user: User = Depends(can_create_or_update)):
    parent = active_or_404(db, Building, payload.building_id, "Building")
    values = payload.model_dump(mode="json")
    values["block_code"] = normalize_code(values["block_code"])
    record = Block(**values, organization_id=parent.organization_id, created_by=user.id, updated_by=user.id)
    db.add(record)
    try:
        db.flush(); audit_change(db, user, AuditAction.CREATE, record, new_values=snapshot(record)); db.commit()
    except IntegrityError as exc:
        db.rollback(); raise HTTPException(status_code=409, detail="Block code already exists in building") from exc
    db.refresh(record); return record


@router.get("/blocks", response_model=list[BlockResponse])
def list_blocks(building_id: int | None = None, skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=500), db: Session = Depends(get_db), _user: User = Depends(can_operational_read)):
    stmt = select(Block).where(Block.deleted_at.is_(None))
    if building_id is not None: stmt = stmt.where(Block.building_id == building_id)
    return db.scalars(pagination(stmt.order_by(Block.building_id, Block.block_code), skip, limit)).all()


@router.get("/blocks/{record_id}", response_model=BlockResponse)
def get_block(record_id: int, db: Session = Depends(get_db), _user: User = Depends(can_operational_read)):
    return active_or_404(db, Block, record_id, "Block")


@router.put("/blocks/{record_id}", response_model=BlockResponse)
def update_block(record_id: int, payload: BlockUpdate, db: Session = Depends(get_db), user: User = Depends(can_create_or_update)):
    changes = payload.model_dump(exclude_unset=True, mode="json")
    if changes.get("block_code"): changes["block_code"] = normalize_code(changes["block_code"])
    return update_record(db, active_or_404(db, Block, record_id, "Block"), changes, user)


@router.delete("/blocks/{record_id}", response_model=BlockResponse)
def delete_block(record_id: int, db: Session = Depends(get_db), user: User = Depends(require_admin)):
    record = active_or_404(db, Block, record_id, "Block")
    if db.scalar(select(Floor.id).where(Floor.block_id == record.id).limit(1)):
        raise HTTPException(status_code=409, detail="Cannot delete block while floors exist")
    return soft_delete(db, record, user)


@router.post("/floors", response_model=FloorResponse, status_code=201)
def create_floor(payload: FloorCreate, db: Session = Depends(get_db), user: User = Depends(can_create_or_update)):
    parent = active_or_404(db, Block, payload.block_id, "Block")
    record = Floor(**payload.model_dump(mode="json"), organization_id=parent.organization_id, created_by=user.id, updated_by=user.id)
    db.add(record)
    try:
        db.flush(); audit_change(db, user, AuditAction.CREATE, record, new_values=snapshot(record)); db.commit()
    except IntegrityError as exc:
        db.rollback(); raise HTTPException(status_code=409, detail="Floor number already exists in block") from exc
    db.refresh(record); return record


@router.get("/floors", response_model=list[FloorResponse])
def list_floors(block_id: int | None = None, skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=500), db: Session = Depends(get_db), _user: User = Depends(can_operational_read)):
    stmt = select(Floor).where(Floor.deleted_at.is_(None))
    if block_id is not None: stmt = stmt.where(Floor.block_id == block_id)
    return db.scalars(pagination(stmt.order_by(Floor.block_id, Floor.floor_no), skip, limit)).all()


@router.get("/floors/{record_id}", response_model=FloorResponse)
def get_floor(record_id: int, db: Session = Depends(get_db), _user: User = Depends(can_operational_read)):
    return active_or_404(db, Floor, record_id, "Floor")


@router.put("/floors/{record_id}", response_model=FloorResponse)
def update_floor(record_id: int, payload: FloorUpdate, db: Session = Depends(get_db), user: User = Depends(can_create_or_update)):
    return update_record(db, active_or_404(db, Floor, record_id, "Floor"), payload.model_dump(exclude_unset=True, mode="json"), user)


@router.delete("/floors/{record_id}", response_model=FloorResponse)
def delete_floor(record_id: int, db: Session = Depends(get_db), user: User = Depends(require_admin)):
    record = active_or_404(db, Floor, record_id, "Floor")
    if db.scalar(select(Room.id).where(Room.floor_id == record.id).limit(1)):
        raise HTTPException(status_code=409, detail="Cannot delete floor while rooms exist")
    return soft_delete(db, record, user)


@router.post("/rooms", response_model=RoomResponse, status_code=201)
def create_room(payload: RoomCreate, db: Session = Depends(get_db), user: User = Depends(can_create_or_update)):
    parent = active_or_404(db, Floor, payload.floor_id, "Floor")
    values = payload.model_dump(mode="json"); values["room_code"] = normalize_code(values["room_code"])
    record = Room(**values, organization_id=parent.organization_id, created_by=user.id, updated_by=user.id)
    db.add(record)
    try:
        db.flush(); audit_change(db, user, AuditAction.CREATE, record, new_values=snapshot(record)); db.commit()
    except IntegrityError as exc:
        db.rollback(); raise HTTPException(status_code=409, detail="Room code already exists") from exc
    db.refresh(record); return record


@router.get("/rooms", response_model=list[RoomResponse])
def list_rooms(floor_id: int | None = None, skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=500), db: Session = Depends(get_db), _user: User = Depends(can_operational_read)):
    stmt = select(Room).where(Room.deleted_at.is_(None))
    if floor_id is not None: stmt = stmt.where(Room.floor_id == floor_id)
    return db.scalars(pagination(stmt.order_by(Room.room_code), skip, limit)).all()


@router.get("/rooms/{record_id}", response_model=RoomResponse)
def get_room(record_id: int, db: Session = Depends(get_db), _user: User = Depends(can_operational_read)):
    return active_or_404(db, Room, record_id, "Room")


@router.put("/rooms/{record_id}", response_model=RoomResponse)
def update_room(record_id: int, payload: RoomUpdate, db: Session = Depends(get_db), user: User = Depends(can_create_or_update)):
    record = active_or_404(db, Room, record_id, "Room", lock=True)
    changes = payload.model_dump(exclude_unset=True, mode="json")
    if changes.get("room_code"): changes["room_code"] = normalize_code(changes["room_code"])
    if "capacity" in changes:
        bed_count = db.scalar(select(func.count()).select_from(Bed).where(Bed.room_id == record.id, Bed.deleted_at.is_(None))) or 0
        if changes["capacity"] < bed_count:
            raise HTTPException(status_code=409, detail="Room capacity cannot be lower than existing bed count")
    return update_record(db, record, changes, user)


@router.delete("/rooms/{record_id}", response_model=RoomResponse)
def delete_room(record_id: int, db: Session = Depends(get_db), user: User = Depends(require_admin)):
    record = active_or_404(db, Room, record_id, "Room")
    if db.scalar(select(Bed.id).where(Bed.room_id == record.id).limit(1)):
        raise HTTPException(status_code=409, detail="Cannot delete room while beds exist")
    return soft_delete(db, record, user)


@router.post("/beds", response_model=BedResponse, status_code=201)
def create_bed(payload: BedCreate, db: Session = Depends(get_db), user: User = Depends(can_create_or_update)):
    room = active_or_404(db, Room, payload.room_id, "Room", lock=True)
    count = db.scalar(select(func.count()).select_from(Bed).where(Bed.room_id == room.id, Bed.deleted_at.is_(None))) or 0
    if count >= room.capacity:
        raise HTTPException(status_code=409, detail="Room capacity has been reached")
    values = payload.model_dump(mode="json"); values["bed_code"] = normalize_code(values["bed_code"])
    if values["status"] == "Occupied":
        raise HTTPException(status_code=422, detail="A bed becomes occupied only through allocation")
    record = Bed(**values, organization_id=room.organization_id, created_by=user.id, updated_by=user.id)
    db.add(record)
    try:
        db.flush(); audit_change(db, user, AuditAction.CREATE, record, new_values=snapshot(record)); db.commit()
    except IntegrityError as exc:
        db.rollback(); raise HTTPException(status_code=409, detail="Bed code already exists") from exc
    db.refresh(record); return record


@router.get("/beds", response_model=list[BedResponse])
def list_beds(room_id: int | None = None, bed_status: str | None = Query(None, alias="status"), skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=500), db: Session = Depends(get_db), _user: User = Depends(can_operational_read)):
    stmt = select(Bed).where(Bed.deleted_at.is_(None))
    if room_id is not None: stmt = stmt.where(Bed.room_id == room_id)
    if bed_status is not None: stmt = stmt.where(Bed.status == bed_status)
    return db.scalars(pagination(stmt.order_by(Bed.bed_code), skip, limit)).all()


@router.get("/beds/{record_id}", response_model=BedResponse)
def get_bed(record_id: int, db: Session = Depends(get_db), _user: User = Depends(can_operational_read)):
    return active_or_404(db, Bed, record_id, "Bed")


@router.put("/beds/{record_id}", response_model=BedResponse)
def update_bed(record_id: int, payload: BedUpdate, db: Session = Depends(get_db), user: User = Depends(can_create_or_update)):
    record = active_or_404(db, Bed, record_id, "Bed", lock=True)
    changes = payload.model_dump(exclude_unset=True, mode="json")
    if changes.get("bed_code"): changes["bed_code"] = normalize_code(changes["bed_code"])
    active = db.scalar(select(BedAllocation.id).where(BedAllocation.bed_id == record.id, BedAllocation.status == "Active"))
    if "status" in changes:
        if active and changes["status"] != "Occupied":
            raise HTTPException(status_code=409, detail="Occupied bed status is controlled by its active allocation")
        if not active and changes["status"] == "Occupied":
            raise HTTPException(status_code=409, detail="Bed cannot be occupied without an active allocation")
    return update_record(db, record, changes, user)


@router.delete("/beds/{record_id}", response_model=BedResponse)
def delete_bed(record_id: int, db: Session = Depends(get_db), user: User = Depends(require_admin)):
    record = active_or_404(db, Bed, record_id, "Bed")
    if db.scalar(select(BedAllocation.id).where(BedAllocation.bed_id == record.id, BedAllocation.status == "Active")):
        raise HTTPException(status_code=409, detail="Cannot delete a bed with an active allocation")
    return soft_delete(db, record, user)


def lock_allocation_target(db: Session, child_id: int, bed_id: int, *, exclude_allocation_id: int | None = None):
    child = db.scalar(select(Child).where(Child.id == child_id).with_for_update())
    if child is None: raise HTTPException(status_code=404, detail="Child not found")
    row = db.execute(
        select(Bed, Room, Floor, Block, Building)
        .join(Room, Room.id == Bed.room_id).join(Floor, Floor.id == Room.floor_id)
        .join(Block, Block.id == Floor.block_id).join(Building, Building.id == Block.building_id)
        .where(Bed.id == bed_id, Bed.deleted_at.is_(None), Room.deleted_at.is_(None), Floor.deleted_at.is_(None), Block.deleted_at.is_(None), Building.deleted_at.is_(None))
        .with_for_update()
    ).first()
    if row is None: raise HTTPException(status_code=404, detail="Bed or accommodation hierarchy not found")
    bed, room, floor, block, building = row
    for item, label in ((building, "Building"), (block, "Block"), (floor, "Floor"), (room, "Room")):
        if item.status != "Active": raise HTTPException(status_code=409, detail=f"{label} is inactive")
    if bed.status != "Vacant": raise HTTPException(status_code=409, detail=f"Bed is {bed.status.lower()}")
    stmt = select(BedAllocation.id).where(BedAllocation.child_id == child_id, BedAllocation.status == "Active")
    if exclude_allocation_id is not None: stmt = stmt.where(BedAllocation.id != exclude_allocation_id)
    if db.scalar(stmt): raise HTTPException(status_code=409, detail="Child already has an active bed allocation")
    if db.scalar(select(BedAllocation.id).where(BedAllocation.bed_id == bed.id, BedAllocation.status == "Active")):
        raise HTTPException(status_code=409, detail="Bed already has an active occupant")
    return child, bed


@router.post("/bed-allocations", response_model=BedAllocationResponse, status_code=201)
def create_bed_allocation(payload: BedAllocationCreate, db: Session = Depends(get_db), user: User = Depends(can_create_or_update)):
    _, bed = lock_allocation_target(db, payload.child_id, payload.bed_id)
    record = BedAllocation(**payload.model_dump(), organization_id=bed.organization_id, status="Active", created_by=user.id, updated_by=user.id)
    bed.status = "Occupied"; bed.updated_by = user.id; db.add(record)
    try:
        db.flush()
        add_audit_log(db, user_id=user.id, action=AuditAction.BED_ALLOCATION, module=AuditModule.BED_ALLOCATIONS, record_id=record.id, new_values=snapshot(record))
        db.commit()
    except IntegrityError as exc:
        db.rollback(); raise HTTPException(status_code=409, detail="Child or bed already has an active allocation") from exc
    db.refresh(record); return record


@router.get("/bed-allocations", response_model=list[BedAllocationResponse])
def list_bed_allocations(child_id: int | None = None, bed_id: int | None = None, allocation_status: str | None = Query(None, alias="status"), skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=500), db: Session = Depends(get_db), _user: User = Depends(can_operational_read)):
    stmt = select(BedAllocation)
    if child_id is not None: stmt = stmt.where(BedAllocation.child_id == child_id)
    if bed_id is not None: stmt = stmt.where(BedAllocation.bed_id == bed_id)
    if allocation_status is not None: stmt = stmt.where(BedAllocation.status == allocation_status)
    return db.scalars(pagination(stmt.order_by(BedAllocation.allocation_date.desc(), BedAllocation.id.desc()), skip, limit)).all()


@router.get("/bed-allocations/{record_id}", response_model=BedAllocationResponse)
def get_bed_allocation(record_id: int, db: Session = Depends(get_db), _user: User = Depends(can_operational_read)):
    record = db.get(BedAllocation, record_id)
    if record is None: raise HTTPException(status_code=404, detail="Bed allocation not found")
    return record


@router.put("/bed-allocations/{record_id}", response_model=BedAllocationResponse)
def update_bed_allocation(record_id: int, payload: BedAllocationUpdate, db: Session = Depends(get_db), user: User = Depends(can_create_or_update)):
    record = db.get(BedAllocation, record_id)
    if record is None: raise HTTPException(status_code=404, detail="Bed allocation not found")
    return update_record(db, record, payload.model_dump(exclude_unset=True), user)


@router.post("/bed-allocations/{record_id}/transfer", response_model=BedTransferResponse)
def transfer_bed(record_id: int, payload: BedTransferRequest, db: Session = Depends(get_db), user: User = Depends(can_create_or_update)):
    current = db.scalar(select(BedAllocation).where(BedAllocation.id == record_id).with_for_update())
    if current is None: raise HTTPException(status_code=404, detail="Bed allocation not found")
    if current.status != "Active": raise HTTPException(status_code=409, detail="Only active allocations can be transferred")
    if payload.transfer_date < current.allocation_date: raise HTTPException(status_code=422, detail="Transfer date cannot precede allocation date")
    if payload.bed_id == current.bed_id: raise HTTPException(status_code=409, detail="Transfer requires a different bed")
    old_bed = active_or_404(db, Bed, current.bed_id, "Current bed", lock=True)
    _, new_bed = lock_allocation_target(db, current.child_id, payload.bed_id, exclude_allocation_id=current.id)
    before = snapshot(current)
    current.status = "Transferred"; current.vacation_date = payload.transfer_date; current.vacation_reason = payload.reason; current.updated_by = user.id
    old_bed.status = "Vacant"; old_bed.updated_by = user.id; db.flush()
    replacement = BedAllocation(
        organization_id=new_bed.organization_id, child_id=current.child_id, bed_id=new_bed.id,
        allocation_date=payload.transfer_date, allocation_reason=f"Transfer: {payload.reason}", notes=payload.notes,
        status="Active", created_by=user.id, updated_by=user.id,
    )
    new_bed.status = "Occupied"; new_bed.updated_by = user.id; db.add(replacement)
    try:
        db.flush()
        add_audit_log(db, user_id=user.id, action=AuditAction.BED_TRANSFER, module=AuditModule.BED_ALLOCATIONS, record_id=current.id, old_values=before, new_values={"previous": snapshot(current), "new": snapshot(replacement)})
        db.commit()
    except IntegrityError as exc:
        db.rollback(); raise HTTPException(status_code=409, detail="Target bed or child allocation conflict") from exc
    db.refresh(current); db.refresh(replacement)
    return BedTransferResponse(previous_allocation=current, new_allocation=replacement)


@router.post("/bed-allocations/{record_id}/vacate", response_model=BedAllocationResponse)
def vacate_bed(record_id: int, payload: BedVacationRequest, db: Session = Depends(get_db), user: User = Depends(can_create_or_update)):
    record = db.scalar(select(BedAllocation).where(BedAllocation.id == record_id).with_for_update())
    if record is None: raise HTTPException(status_code=404, detail="Bed allocation not found")
    if record.status != "Active": raise HTTPException(status_code=409, detail="Only active allocations can be vacated")
    if payload.vacation_date < record.allocation_date: raise HTTPException(status_code=422, detail="Vacation date cannot precede allocation date")
    bed = active_or_404(db, Bed, record.bed_id, "Bed", lock=True); before = snapshot(record)
    record.status = "Vacated"; record.vacation_date = payload.vacation_date; record.vacation_reason = payload.reason
    if payload.notes is not None: record.notes = payload.notes
    record.updated_by = user.id; bed.status = "Vacant"; bed.updated_by = user.id
    add_audit_log(db, user_id=user.id, action=AuditAction.BED_VACATION, module=AuditModule.BED_ALLOCATIONS, record_id=record.id, old_values=before, new_values=snapshot(record))
    db.commit(); db.refresh(record); return record


def occupancy_counts(db: Session) -> dict[str, int]:
    rows = db.execute(select(Bed.status, func.count(Bed.id)).where(Bed.deleted_at.is_(None)).group_by(Bed.status)).all()
    counts = {"Vacant": 0, "Occupied": 0, "Reserved": 0, "Maintenance": 0}
    counts.update(dict(rows)); return counts


def occupancy_result(scope_id: int | None, code: str, name: str, counts: dict[str, int]) -> OccupancyResponse:
    total = sum(counts.values()); occupied = counts.get("Occupied", 0)
    return OccupancyResponse(scope_id=scope_id, scope_code=code, scope_name=name, total_beds=total,
        occupied_beds=occupied, vacant_beds=counts.get("Vacant", 0), reserved_beds=counts.get("Reserved", 0),
        maintenance_beds=counts.get("Maintenance", 0), occupancy_percentage=round(occupied * 100 / total, 2) if total else 0.0)


def grouped_occupancy(db: Session, scope: str) -> list[OccupancyResponse]:
    if scope == "building":
        entities = db.scalars(select(Building).where(Building.deleted_at.is_(None)).order_by(Building.building_code)).all()
        rows = db.execute(select(Block.building_id, Bed.status, func.count(Bed.id)).join(Floor, Floor.block_id == Block.id).join(Room, Room.floor_id == Floor.id).join(Bed, Bed.room_id == Room.id).where(Block.deleted_at.is_(None), Floor.deleted_at.is_(None), Room.deleted_at.is_(None), Bed.deleted_at.is_(None)).group_by(Block.building_id, Bed.status)).all()
        attrs = ("building_code", "building_name")
    elif scope == "block":
        entities = db.scalars(select(Block).where(Block.deleted_at.is_(None)).order_by(Block.block_code)).all()
        rows = db.execute(select(Floor.block_id, Bed.status, func.count(Bed.id)).join(Room, Room.floor_id == Floor.id).join(Bed, Bed.room_id == Room.id).where(Floor.deleted_at.is_(None), Room.deleted_at.is_(None), Bed.deleted_at.is_(None)).group_by(Floor.block_id, Bed.status)).all()
        attrs = ("block_code", "block_name")
    else:
        entities = db.scalars(select(Floor).where(Floor.deleted_at.is_(None)).order_by(Floor.floor_no)).all()
        rows = db.execute(select(Room.floor_id, Bed.status, func.count(Bed.id)).join(Bed, Bed.room_id == Room.id).where(Room.deleted_at.is_(None), Bed.deleted_at.is_(None)).group_by(Room.floor_id, Bed.status)).all()
        attrs = ("floor_no", "floor_name")
    mapped: dict[int, dict[str, int]] = {}
    for entity_id, bed_status, count in rows: mapped.setdefault(entity_id, {})[bed_status] = count
    return [occupancy_result(entity.id, str(getattr(entity, attrs[0])), getattr(entity, attrs[1]), mapped.get(entity.id, {})) for entity in entities]


@router.get("/reports/buildings", response_model=list[BuildingResponse], tags=["Accommodation Reports"])
def report_buildings(db: Session = Depends(get_db), _user: User = Depends(can_operational_read)): return db.scalars(select(Building).where(Building.deleted_at.is_(None)).order_by(Building.building_code)).all()
@router.get("/reports/blocks", response_model=list[BlockResponse], tags=["Accommodation Reports"])
def report_blocks(db: Session = Depends(get_db), _user: User = Depends(can_operational_read)): return db.scalars(select(Block).where(Block.deleted_at.is_(None)).order_by(Block.block_code)).all()
@router.get("/reports/floors", response_model=list[FloorResponse], tags=["Accommodation Reports"])
def report_floors(db: Session = Depends(get_db), _user: User = Depends(can_operational_read)): return db.scalars(select(Floor).where(Floor.deleted_at.is_(None)).order_by(Floor.block_id, Floor.floor_no)).all()
@router.get("/reports/rooms", response_model=list[RoomResponse], tags=["Accommodation Reports"])
def report_rooms(db: Session = Depends(get_db), _user: User = Depends(can_operational_read)): return db.scalars(select(Room).where(Room.deleted_at.is_(None)).order_by(Room.room_code)).all()
@router.get("/reports/beds", response_model=list[BedResponse], tags=["Accommodation Reports"])
def report_beds(db: Session = Depends(get_db), _user: User = Depends(can_operational_read)): return db.scalars(select(Bed).where(Bed.deleted_at.is_(None)).order_by(Bed.bed_code)).all()


@router.get("/reports/occupancy", response_model=OccupancyResponse, tags=["Accommodation Reports"])
def report_occupancy(db: Session = Depends(get_db), _user: User = Depends(can_operational_read)): return occupancy_result(None, "ALL", "All Accommodation", occupancy_counts(db))
@router.get("/reports/building-occupancy", response_model=list[OccupancyResponse], tags=["Accommodation Reports"])
def report_building_occupancy(db: Session = Depends(get_db), _user: User = Depends(can_operational_read)): return grouped_occupancy(db, "building")
@router.get("/reports/block-occupancy", response_model=list[OccupancyResponse], tags=["Accommodation Reports"])
def report_block_occupancy(db: Session = Depends(get_db), _user: User = Depends(can_operational_read)): return grouped_occupancy(db, "block")
@router.get("/reports/floor-occupancy", response_model=list[OccupancyResponse], tags=["Accommodation Reports"])
def report_floor_occupancy(db: Session = Depends(get_db), _user: User = Depends(can_operational_read)): return grouped_occupancy(db, "floor")
@router.get("/reports/vacant-beds", response_model=list[BedResponse], tags=["Accommodation Reports"])
def report_vacant_beds(db: Session = Depends(get_db), _user: User = Depends(can_operational_read)): return db.scalars(select(Bed).where(Bed.deleted_at.is_(None), Bed.status == "Vacant").order_by(Bed.bed_code)).all()
@router.get("/reports/occupied-beds", response_model=list[BedResponse], tags=["Accommodation Reports"])
def report_occupied_beds(db: Session = Depends(get_db), _user: User = Depends(can_operational_read)): return db.scalars(select(Bed).where(Bed.deleted_at.is_(None), Bed.status == "Occupied").order_by(Bed.bed_code)).all()


@router.get("/reports/children-without-beds", response_model=list[ChildWithoutBedResponse], tags=["Accommodation Reports"])
def report_children_without_beds(db: Session = Depends(get_db), _user: User = Depends(can_operational_read)):
    active = select(BedAllocation.id).where(BedAllocation.child_id == Child.id, BedAllocation.status == "Active")
    children = db.scalars(select(Child).where(not_(active.exists())).order_by(Child.full_name)).all()
    return [ChildWithoutBedResponse(id=c.id, child_id=c.child_id, full_name=c.full_name, status=c.status) for c in children]


@router.get("/dashboard/accommodation", response_model=AccommodationDashboard, tags=["Accommodation Dashboard"])
def accommodation_dashboard(db: Session = Depends(get_db), _user: User = Depends(can_operational_read)):
    def count(model): return db.scalar(select(func.count()).select_from(model).where(model.deleted_at.is_(None))) or 0
    bed_counts = occupancy_counts(db); total_beds = sum(bed_counts.values()); occupied = bed_counts["Occupied"]
    active = select(BedAllocation.id).where(BedAllocation.child_id == Child.id, BedAllocation.status == "Active")
    children_without = db.scalar(select(func.count()).select_from(Child).where(not_(active.exists()))) or 0
    return AccommodationDashboard(total_buildings=count(Building), total_blocks=count(Block), total_floors=count(Floor),
        total_rooms=count(Room), total_beds=total_beds, occupied_beds=occupied, vacant_beds=bed_counts["Vacant"],
        reserved_beds=bed_counts["Reserved"], maintenance_beds=bed_counts["Maintenance"], children_without_beds=children_without,
        occupancy_percentage=round(occupied * 100 / total_beds, 2) if total_beds else 0.0)
