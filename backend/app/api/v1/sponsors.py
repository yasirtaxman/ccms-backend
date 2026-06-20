from datetime import UTC, date, datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, not_, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.deps import (
    can_create_or_update,
    can_sponsor_read,
    get_db,
    ROLE_ADMIN,
    ROLE_DATA_ENTRY,
    ROLE_MANAGER,
    require_admin,
)
from app.models.child import Child
from app.models.sponsor import ChildSponsorship, Sponsor
from app.models.user import User
from app.schemas.sponsor import (
    ChildSponsorshipCreate,
    ChildSponsorshipResponse,
    ChildSponsorshipUpdate,
    ChildWithoutSponsorResponse,
    SponsorCreate,
    SponsorResponse,
    SponsorSearchResponse,
    SponsorUpdate,
    SponsoredChildResponse,
    SponsorStatus,
    SponsorType,
    SponsorViewerResponse,
)
from app.services.audit import AuditAction, AuditModule, add_audit_log

router = APIRouter(tags=["Sponsors"])
SponsorVisibleResponse = SponsorResponse | SponsorViewerResponse


def sponsor_values(sponsor: Sponsor) -> dict:
    return SponsorResponse.model_validate(sponsor).model_dump(mode="json")


def user_can_view_sensitive_sponsor_data(user: User) -> bool:
    privileged_roles = {ROLE_ADMIN, ROLE_MANAGER, ROLE_DATA_ENTRY}
    role_names = {role.name for role in user.roles}
    return bool(role_names & privileged_roles)


def sponsor_for_user(sponsor: Sponsor, user: User) -> SponsorVisibleResponse:
    if user_can_view_sensitive_sponsor_data(user):
        return SponsorResponse.model_validate(sponsor)
    return SponsorViewerResponse.model_validate(sponsor)


def sponsorship_values(sponsorship: ChildSponsorship) -> dict:
    return ChildSponsorshipResponse.model_validate(sponsorship).model_dump(mode="json")


def get_sponsor_or_404(db: Session, sponsor_id: int) -> Sponsor:
    sponsor = db.scalar(
        select(Sponsor).where(Sponsor.id == sponsor_id, Sponsor.deleted_at.is_(None))
    )
    if sponsor is None:
        raise HTTPException(status_code=404, detail="Sponsor not found")
    return sponsor


def get_sponsorship_or_404(db: Session, sponsorship_id: int) -> ChildSponsorship:
    sponsorship = db.get(ChildSponsorship, sponsorship_id)
    if sponsorship is None:
        raise HTTPException(status_code=404, detail="Sponsorship not found")
    return sponsorship


def ensure_no_sponsorship_overlap(
    db: Session,
    *,
    child_id: int,
    sponsor_id: int,
    start_date: date,
    end_date: date | None,
    exclude_id: int | None = None,
) -> None:
    filters = [
        ChildSponsorship.child_id == child_id,
        ChildSponsorship.sponsor_id == sponsor_id,
        or_(ChildSponsorship.end_date.is_(None), ChildSponsorship.end_date >= start_date),
    ]
    if end_date is not None:
        filters.append(ChildSponsorship.start_date <= end_date)
    if exclude_id is not None:
        filters.append(ChildSponsorship.id != exclude_id)
    if db.scalar(select(ChildSponsorship.id).where(*filters).limit(1)):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Sponsorship period overlaps an existing sponsorship for this child and sponsor",
        )


def raise_sponsorship_integrity_error(exc: IntegrityError) -> None:
    if "excl_child_sponsorships_period" in str(exc.orig):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Sponsorship period overlaps an existing sponsorship for this child and sponsor",
        ) from exc
    raise HTTPException(status_code=422, detail="Invalid sponsorship data") from exc


@router.post(
    "/sponsors",
    response_model=SponsorResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a sponsor",
)
def create_sponsor(
    payload: SponsorCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(can_create_or_update),
):
    if db.scalar(select(Sponsor.id).where(Sponsor.sponsor_code == payload.sponsor_code)):
        raise HTTPException(status_code=409, detail="Sponsor code already exists")

    sponsor = Sponsor(
        **payload.model_dump(mode="json"),
        created_by=current_user.id,
        updated_by=current_user.id,
    )
    db.add(sponsor)
    try:
        db.flush()
        add_audit_log(
            db,
            user_id=current_user.id,
            action=AuditAction.CREATE,
            module=AuditModule.SPONSORS,
            record_id=sponsor.id,
            new_values=sponsor_values(sponsor),
        )
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Sponsor code already exists")
    db.refresh(sponsor)
    return sponsor


@router.get(
    "/sponsors/search",
    response_model=SponsorSearchResponse,
    summary="Search sponsors",
)
def search_sponsors(
    sponsor_code: str | None = Query(default=None, max_length=50),
    name: str | None = Query(default=None, max_length=255),
    mobile: str | None = Query(default=None, max_length=30),
    email: str | None = Query(default=None, max_length=255),
    status_filter: SponsorStatus | None = Query(default=None, alias="status"),
    sponsor_type: SponsorType | None = None,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
    _current_user: User = Depends(can_sponsor_read),
):
    filters = []
    if sponsor_code:
        filters.append(Sponsor.sponsor_code.ilike(f"%{sponsor_code.strip()}%"))
    if name:
        pattern = f"%{name.strip()}%"
        filters.append(
            or_(Sponsor.full_name.ilike(pattern), Sponsor.organization_name.ilike(pattern))
        )
    if mobile:
        filters.append(
            or_(Sponsor.mobile.ilike(f"%{mobile}%"), Sponsor.alternate_mobile.ilike(f"%{mobile}%"))
        )
    if email:
        filters.append(Sponsor.email.ilike(f"%{email.strip()}%"))
    if status_filter:
        filters.append(Sponsor.status == status_filter.value)
    if sponsor_type:
        filters.append(Sponsor.sponsor_type == sponsor_type.value)
    if not user_can_view_sensitive_sponsor_data(_current_user) and (mobile or email):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Viewer role cannot search sensitive sponsor contact fields",
        )

    total = db.scalar(
        select(func.count())
        .select_from(Sponsor)
        .where(Sponsor.deleted_at.is_(None), *filters)
    ) or 0
    items = db.scalars(
        select(Sponsor)
        .where(Sponsor.deleted_at.is_(None), *filters)
        .order_by(Sponsor.sponsor_code)
        .offset(skip)
        .limit(limit)
    ).all()
    return SponsorSearchResponse(
        items=[sponsor_for_user(item, _current_user) for item in items],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get("/sponsors", response_model=list[SponsorVisibleResponse], summary="List sponsors")
def list_sponsors(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
    _current_user: User = Depends(can_sponsor_read),
):
    sponsors = db.scalars(
        select(Sponsor)
        .where(Sponsor.deleted_at.is_(None))
        .order_by(Sponsor.sponsor_code)
        .offset(skip)
        .limit(limit)
    ).all()
    return [sponsor_for_user(item, _current_user) for item in sponsors]


@router.get(
    "/sponsors/{sponsor_id}",
    response_model=SponsorVisibleResponse,
    summary="Get a sponsor",
)
def get_sponsor(
    sponsor_id: int,
    db: Session = Depends(get_db),
    _current_user: User = Depends(can_sponsor_read),
):
    return sponsor_for_user(get_sponsor_or_404(db, sponsor_id), _current_user)


@router.put(
    "/sponsors/{sponsor_id}",
    response_model=SponsorResponse,
    summary="Update a sponsor",
)
def update_sponsor(
    sponsor_id: int,
    payload: SponsorUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(can_create_or_update),
):
    sponsor = get_sponsor_or_404(db, sponsor_id)
    changes = payload.model_dump(exclude_unset=True, mode="json")
    if not changes:
        return sponsor
    if "sponsor_code" in changes and db.scalar(
        select(Sponsor.id).where(
            Sponsor.sponsor_code == changes["sponsor_code"], Sponsor.id != sponsor_id
        )
    ):
        raise HTTPException(status_code=409, detail="Sponsor code already exists")

    old_values = {key: getattr(sponsor, key) for key in changes}
    for key, value in changes.items():
        setattr(sponsor, key, value)
    sponsor.updated_by = current_user.id
    add_audit_log(
        db,
        user_id=current_user.id,
        action=AuditAction.UPDATE,
        module=AuditModule.SPONSORS,
        record_id=sponsor.id,
        old_values=old_values,
        new_values=changes,
    )
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Sponsor code already exists")
    db.refresh(sponsor)
    return sponsor


@router.delete(
    "/sponsors/{sponsor_id}",
    response_model=SponsorResponse,
    summary="Delete a sponsor while preserving history",
)
def delete_sponsor(
    sponsor_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    sponsor = get_sponsor_or_404(db, sponsor_id)
    old_values = sponsor_values(sponsor)
    sponsor.deleted_at = datetime.now(UTC)
    sponsor.deleted_by = current_user.id
    sponsor.updated_by = current_user.id
    add_audit_log(
        db,
        user_id=current_user.id,
        action=AuditAction.DELETE,
        module=AuditModule.SPONSORS,
        record_id=sponsor.id,
        old_values=old_values,
        new_values={
            "deleted_at": sponsor.deleted_at,
            "deleted_by": current_user.id,
            "updated_by": current_user.id,
        },
    )
    db.commit()
    db.refresh(sponsor)
    return sponsor


@router.post(
    "/children/{child_id}/sponsorships",
    response_model=ChildSponsorshipResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a child sponsorship",
)
def create_sponsorship(
    child_id: int,
    payload: ChildSponsorshipCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(can_create_or_update),
):
    if db.get(Child, child_id) is None:
        raise HTTPException(status_code=404, detail="Child not found")
    sponsor = get_sponsor_or_404(db, payload.sponsor_id)
    if sponsor.status != SponsorStatus.ACTIVE.value:
        raise HTTPException(status_code=409, detail="Sponsor must be active")

    ensure_no_sponsorship_overlap(
        db,
        child_id=child_id,
        sponsor_id=sponsor.id,
        start_date=payload.start_date,
        end_date=payload.end_date,
    )

    sponsorship = ChildSponsorship(
        child_id=child_id,
        organization_id=sponsor.organization_id,
        **payload.model_dump(),
        created_by=current_user.id,
        updated_by=current_user.id,
    )
    db.add(sponsorship)
    try:
        db.flush()
        add_audit_log(
            db,
            user_id=current_user.id,
            action=AuditAction.CREATE,
            module=AuditModule.SPONSORSHIPS,
            record_id=sponsorship.id,
            new_values=sponsorship_values(sponsorship),
        )
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise_sponsorship_integrity_error(exc)
    db.refresh(sponsorship)
    return sponsorship


@router.get(
    "/children/{child_id}/sponsorships",
    response_model=list[ChildSponsorshipResponse],
    summary="Get complete sponsorship history for a child",
)
def list_child_sponsorships(
    child_id: int,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
    _current_user: User = Depends(can_sponsor_read),
):
    if db.get(Child, child_id) is None:
        raise HTTPException(status_code=404, detail="Child not found")
    return db.scalars(
        select(ChildSponsorship)
        .where(ChildSponsorship.child_id == child_id)
        .order_by(ChildSponsorship.start_date.desc(), ChildSponsorship.id.desc())
        .offset(skip)
        .limit(limit)
    ).all()


@router.get(
    "/sponsors/{sponsor_id}/children",
    response_model=list[SponsoredChildResponse],
    summary="Get children and sponsorship history for a sponsor",
)
def list_sponsor_children(
    sponsor_id: int,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
    _current_user: User = Depends(can_sponsor_read),
):
    get_sponsor_or_404(db, sponsor_id)
    rows = db.execute(
        select(ChildSponsorship, Child)
        .join(Child, Child.id == ChildSponsorship.child_id)
        .where(ChildSponsorship.sponsor_id == sponsor_id)
        .order_by(ChildSponsorship.start_date.desc(), ChildSponsorship.id.desc())
        .offset(skip)
        .limit(limit)
    ).all()
    return [
        SponsoredChildResponse(
            sponsorship_id=sponsorship.id,
            child_id=child.id,
            child_code=child.child_id,
            child_name=child.full_name,
            start_date=sponsorship.start_date,
            end_date=sponsorship.end_date,
            status=sponsorship.status,
            sponsorship_type=sponsorship.sponsorship_type,
        )
        for sponsorship, child in rows
    ]


@router.put(
    "/sponsorships/{sponsorship_id}",
    response_model=ChildSponsorshipResponse,
    summary="Update a sponsorship or change its status",
)
def update_sponsorship(
    sponsorship_id: int,
    payload: ChildSponsorshipUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(can_create_or_update),
):
    sponsorship = get_sponsorship_or_404(db, sponsorship_id)
    changes = payload.model_dump(exclude_unset=True)
    if not changes:
        return sponsorship
    effective_start = changes.get("start_date", sponsorship.start_date)
    effective_end = changes.get("end_date", sponsorship.end_date)
    if effective_end is not None and effective_end < effective_start:
        raise HTTPException(status_code=422, detail="end_date must be on or after start_date")
    if "start_date" in changes or "end_date" in changes:
        ensure_no_sponsorship_overlap(
            db,
            child_id=sponsorship.child_id,
            sponsor_id=sponsorship.sponsor_id,
            start_date=effective_start,
            end_date=effective_end,
            exclude_id=sponsorship.id,
        )

    old_values = {key: getattr(sponsorship, key) for key in changes}
    status_changed = "status" in changes and changes["status"] != sponsorship.status
    for key, value in changes.items():
        setattr(sponsorship, key, value)
    sponsorship.updated_by = current_user.id
    add_audit_log(
        db,
        user_id=current_user.id,
        action=(
            AuditAction.SPONSORSHIP_STATUS_CHANGE
            if status_changed
            else AuditAction.UPDATE
        ),
        module=AuditModule.SPONSORSHIPS,
        record_id=sponsorship.id,
        old_values=old_values,
        new_values=changes,
    )
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise_sponsorship_integrity_error(exc)
    db.refresh(sponsorship)
    return sponsorship


@router.get(
    "/reports/sponsors",
    response_model=SponsorSearchResponse,
    tags=["Sponsor Reports"],
    summary="Sponsor master report",
)
def sponsor_report(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
    _current_user: User = Depends(can_sponsor_read),
):
    total = db.scalar(
        select(func.count()).select_from(Sponsor).where(Sponsor.deleted_at.is_(None))
    ) or 0
    items = db.scalars(
        select(Sponsor)
        .where(Sponsor.deleted_at.is_(None))
        .order_by(Sponsor.sponsor_code)
        .offset(skip)
        .limit(limit)
    ).all()
    return SponsorSearchResponse(
        items=[sponsor_for_user(item, _current_user) for item in items],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/reports/active-sponsorships",
    response_model=list[ChildSponsorshipResponse],
    tags=["Sponsor Reports"],
    summary="Currently active sponsorships",
)
def active_sponsorship_report(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
    _current_user: User = Depends(can_sponsor_read),
):
    today = date.today()
    return db.scalars(
        select(ChildSponsorship)
        .where(
            ChildSponsorship.status == "Active",
            ChildSponsorship.start_date <= today,
            or_(ChildSponsorship.end_date.is_(None), ChildSponsorship.end_date >= today),
        )
        .order_by(ChildSponsorship.start_date.desc())
        .offset(skip)
        .limit(limit)
    ).all()


@router.get(
    "/reports/expired-sponsorships",
    response_model=list[ChildSponsorshipResponse],
    tags=["Sponsor Reports"],
    summary="Sponsorships whose end date has passed",
)
def expired_sponsorship_report(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
    _current_user: User = Depends(can_sponsor_read),
):
    return db.scalars(
        select(ChildSponsorship)
        .where(ChildSponsorship.end_date < date.today())
        .order_by(ChildSponsorship.end_date.desc())
        .offset(skip)
        .limit(limit)
    ).all()


@router.get(
    "/reports/children-without-sponsors",
    response_model=list[ChildWithoutSponsorResponse],
    tags=["Sponsor Reports"],
    summary="Children without a currently active sponsorship",
)
def children_without_sponsors_report(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
    _current_user: User = Depends(can_sponsor_read),
):
    today = date.today()
    active_sponsorship = select(ChildSponsorship.id).where(
        ChildSponsorship.child_id == Child.id,
        ChildSponsorship.status == "Active",
        ChildSponsorship.start_date <= today,
        or_(ChildSponsorship.end_date.is_(None), ChildSponsorship.end_date >= today),
    )
    children = db.scalars(
        select(Child)
        .where(not_(active_sponsorship.exists()))
        .order_by(Child.full_name)
        .offset(skip)
        .limit(limit)
    ).all()
    return [
        ChildWithoutSponsorResponse(
            id=child.id,
            child_id=child.child_id,
            full_name=child.full_name,
            status=child.status,
        )
        for child in children
    ]
