from datetime import UTC, date, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.encoders import jsonable_encoder
from sqlalchemy import func, not_, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.inspection import inspect
from sqlalchemy.orm import Session

from app.core.deps import (
    ROLE_ADMIN,
    ROLE_DATA_ENTRY,
    ROLE_MANAGER,
    can_create_or_update,
    can_operational_read,
    get_db,
    require_admin,
    require_manager,
)
from app.models.case_management import (
    CarePlan,
    CaseNote,
    CaseReview,
    ChildCaseProfile,
    CounselingSession,
    IncidentRecord,
)
from app.models.child import Child
from app.models.user import User
from app.schemas.case_management import (
    CarePlanCreate,
    CarePlanResponse,
    CarePlanUpdate,
    CaseDashboardResponse,
    CaseNoteCreate,
    CaseNoteResponse,
    CaseNoteUpdate,
    CaseReviewCreate,
    CaseReviewResponse,
    CaseReviewUpdate,
    ChildCaseProfileCreate,
    ChildCaseProfileResponse,
    ChildCaseProfileUpdate,
    CounselingSessionCreate,
    CounselingSessionResponse,
    CounselingSessionUpdate,
    IncidentRecordCreate,
    IncidentRecordResponse,
    IncidentRecordUpdate,
    IncidentReviewRequest,
    IncidentReviewStatus,
    IncidentType,
    NoteType,
    NoteVisibility,
    RiskLevel,
    Severity,
)
from app.services.audit import AuditAction, AuditModule, add_audit_log

router = APIRouter(tags=["Case Management"])


def snapshot(instance) -> dict:
    return jsonable_encoder(
        {column.key: getattr(instance, column.key) for column in inspect(instance).mapper.column_attrs}
    )


def role_names(user: User) -> set[str]:
    return {role.name for role in user.roles}


def is_admin(user: User) -> bool:
    return ROLE_ADMIN in role_names(user)


def allowed_note_visibilities(user: User) -> set[str]:
    roles = role_names(user)
    if roles & {ROLE_ADMIN, ROLE_MANAGER}:
        return {"Normal", "Confidential", "Restricted"}
    if ROLE_DATA_ENTRY in roles:
        return {"Normal", "Confidential"}
    return {"Normal"}


def child_or_404(db: Session, child_id: int) -> Child:
    child = db.get(Child, child_id)
    if child is None:
        raise HTTPException(status_code=404, detail="Child not found")
    return child


def active_or_404(db: Session, model, record_id: int, label: str):
    record = db.scalar(select(model).where(model.id == record_id, model.deleted_at.is_(None)))
    if record is None:
        raise HTTPException(status_code=404, detail=f"{label} not found")
    return record


def profile_for_child(db: Session, child_id: int) -> ChildCaseProfile:
    profile = db.scalar(
        select(ChildCaseProfile).where(
            ChildCaseProfile.child_id == child_id,
            ChildCaseProfile.deleted_at.is_(None),
        )
    )
    if profile is None:
        raise HTTPException(status_code=404, detail="Case profile not found")
    return profile


def validate_profile_link(db: Session, profile_id: int | None, child_id: int) -> None:
    if profile_id is None:
        return
    profile = active_or_404(db, ChildCaseProfile, profile_id, "Case profile")
    if profile.child_id != child_id:
        raise HTTPException(status_code=422, detail="Case profile does not belong to child")


def audit_case(
    db: Session,
    user: User,
    action: AuditAction,
    module: AuditModule,
    record_id: int,
    *,
    old_values: dict | None = None,
    new_values: dict | None = None,
) -> None:
    add_audit_log(db, user_id=user.id, action=action, module=module, record_id=record_id,
                  old_values=old_values, new_values=new_values)


def commit_or_conflict(db: Session, detail: str) -> None:
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail=detail) from exc


def update_record(db: Session, record, changes: dict, user: User, action: AuditAction, module: AuditModule):
    if not changes:
        return record
    old = {key: getattr(record, key) for key in changes}
    for key, value in changes.items():
        setattr(record, key, value)
    record.updated_by = user.id
    audit_case(db, user, action, module, record.id, old_values=old, new_values=changes)
    commit_or_conflict(db, "Duplicate or invalid case-management data")
    db.refresh(record)
    return record


def soft_delete(db: Session, record, user: User, action: AuditAction, module: AuditModule):
    old = snapshot(record)
    record.deleted_at = datetime.now(UTC)
    record.deleted_by = user.id
    record.updated_by = user.id
    audit_case(db, user, action, module, record.id, old_values=old,
               new_values={"deleted_at": record.deleted_at, "deleted_by": user.id})
    db.commit()
    db.refresh(record)
    return record


@router.post("/children/{child_id}/case-profile", response_model=ChildCaseProfileResponse, status_code=201, summary="Create a child case profile")
def create_case_profile(child_id: int, payload: ChildCaseProfileCreate, db: Session = Depends(get_db), user: User = Depends(can_create_or_update)):
    child_or_404(db, child_id)
    if payload.case_status.value == "Closed" and not (role_names(user) & {ROLE_ADMIN, ROLE_MANAGER}):
        raise HTTPException(status_code=403, detail="Only Admin or Manager can create a closed case")
    if db.scalar(select(ChildCaseProfile.id).where(ChildCaseProfile.child_id == child_id)):
        raise HTTPException(status_code=409, detail="Child already has a case profile")
    values = payload.model_dump()
    values["case_number"] = values["case_number"].strip().upper()
    record = ChildCaseProfile(child_id=child_id, **values, created_by=user.id, updated_by=user.id)
    db.add(record)
    try:
        db.flush(); audit_case(db, user, AuditAction.CASE_PROFILE_CREATE, AuditModule.CASE_PROFILE, record.id, new_values=snapshot(record)); db.commit()
    except IntegrityError as exc:
        db.rollback(); raise HTTPException(status_code=409, detail="Child profile or case number already exists") from exc
    db.refresh(record); return record


@router.get("/children/{child_id}/case-profile", response_model=ChildCaseProfileResponse)
def get_case_profile(child_id: int, db: Session = Depends(get_db), _user: User = Depends(can_operational_read)):
    child_or_404(db, child_id); return profile_for_child(db, child_id)


@router.put("/children/{child_id}/case-profile", response_model=ChildCaseProfileResponse)
def update_case_profile(child_id: int, payload: ChildCaseProfileUpdate, db: Session = Depends(get_db), user: User = Depends(can_create_or_update)):
    record = profile_for_child(db, child_id)
    if record.case_status == "Closed" and not is_admin(user):
        raise HTTPException(status_code=403, detail="Closed cases can only be updated by Admin")
    changes = payload.model_dump(exclude_unset=True)
    if changes.get("case_number"):
        changes["case_number"] = changes["case_number"].strip().upper()
    if changes.get("case_status") == "Closed" and record.case_status != "Closed":
        raise HTTPException(status_code=409, detail="Use the case close endpoint")
    if record.case_status == "Closed" and "case_status" in changes and changes["case_status"] != "Closed":
        raise HTTPException(status_code=409, detail="Use the case reopen endpoint")
    return update_record(db, record, changes, user, AuditAction.CASE_PROFILE_UPDATE, AuditModule.CASE_PROFILE)


@router.post("/children/{child_id}/case-profile/close", response_model=ChildCaseProfileResponse)
def close_case_profile(child_id: int, db: Session = Depends(get_db), user: User = Depends(require_manager)):
    record = profile_for_child(db, child_id)
    if record.case_status == "Closed":
        raise HTTPException(status_code=409, detail="Case is already closed")
    return update_record(db, record, {"case_status": "Closed"}, user, AuditAction.CASE_PROFILE_CLOSE, AuditModule.CASE_PROFILE)


@router.post("/children/{child_id}/case-profile/reopen", response_model=ChildCaseProfileResponse)
def reopen_case_profile(child_id: int, db: Session = Depends(get_db), user: User = Depends(require_admin)):
    record = profile_for_child(db, child_id)
    if record.case_status != "Closed":
        raise HTTPException(status_code=409, detail="Only closed cases can be reopened")
    return update_record(db, record, {"case_status": "Open"}, user, AuditAction.CASE_PROFILE_REOPEN, AuditModule.CASE_PROFILE)


@router.post("/children/{child_id}/case-notes", response_model=CaseNoteResponse, status_code=201)
def create_case_note(child_id: int, payload: CaseNoteCreate, db: Session = Depends(get_db), user: User = Depends(can_create_or_update)):
    child_or_404(db, child_id); validate_profile_link(db, payload.case_profile_id, child_id)
    if payload.visibility.value not in allowed_note_visibilities(user):
        raise HTTPException(status_code=403, detail="Not authorized for requested note visibility")
    record = CaseNote(child_id=child_id, **payload.model_dump(), created_by=user.id, updated_by=user.id)
    db.add(record); db.flush(); audit_case(db, user, AuditAction.CASE_NOTE_CREATE, AuditModule.CASE_NOTE, record.id, new_values=snapshot(record)); db.commit(); db.refresh(record)
    return record


@router.get("/children/{child_id}/case-notes", response_model=list[CaseNoteResponse])
def list_case_notes(child_id: int, note_type: NoteType | None = None, visibility: NoteVisibility | None = None, follow_up_required: bool | None = None, from_date: date | None = None, to_date: date | None = None, db: Session = Depends(get_db), user: User = Depends(can_operational_read)):
    child_or_404(db, child_id)
    allowed = allowed_note_visibilities(user)
    if visibility is not None and visibility.value not in allowed:
        raise HTTPException(status_code=403, detail="Not authorized for requested note visibility")
    stmt = select(CaseNote).where(CaseNote.child_id == child_id, CaseNote.deleted_at.is_(None), CaseNote.visibility.in_(allowed))
    if note_type: stmt = stmt.where(CaseNote.note_type == note_type.value)
    if visibility: stmt = stmt.where(CaseNote.visibility == visibility.value)
    if follow_up_required is not None: stmt = stmt.where(CaseNote.follow_up_required == follow_up_required)
    if from_date: stmt = stmt.where(CaseNote.note_date >= from_date)
    if to_date: stmt = stmt.where(CaseNote.note_date <= to_date)
    return db.scalars(stmt.order_by(CaseNote.note_date.desc(), CaseNote.id.desc())).all()


def visible_note_or_404(db: Session, note_id: int, user: User) -> CaseNote:
    note = active_or_404(db, CaseNote, note_id, "Case note")
    if note.visibility not in allowed_note_visibilities(user):
        raise HTTPException(status_code=404, detail="Case note not found")
    return note


@router.get("/case-notes/{note_id}", response_model=CaseNoteResponse)
def get_case_note(note_id: int, db: Session = Depends(get_db), user: User = Depends(can_operational_read)):
    return visible_note_or_404(db, note_id, user)


@router.put("/case-notes/{note_id}", response_model=CaseNoteResponse)
def update_case_note(note_id: int, payload: CaseNoteUpdate, db: Session = Depends(get_db), user: User = Depends(can_create_or_update)):
    record = visible_note_or_404(db, note_id, user); changes = payload.model_dump(exclude_unset=True)
    target_visibility = changes.get("visibility", record.visibility)
    if target_visibility not in allowed_note_visibilities(user):
        raise HTTPException(status_code=403, detail="Not authorized for requested note visibility")
    note_date = changes.get("note_date", record.note_date); follow_date = changes.get("follow_up_date", record.follow_up_date)
    follow_required = changes.get("follow_up_required", record.follow_up_required)
    if follow_date is not None and follow_date < note_date: raise HTTPException(status_code=422, detail="follow_up_date cannot be before note_date")
    if follow_required and follow_date is None: raise HTTPException(status_code=422, detail="follow_up_date required")
    return update_record(db, record, changes, user, AuditAction.CASE_NOTE_UPDATE, AuditModule.CASE_NOTE)


@router.delete("/case-notes/{note_id}", response_model=CaseNoteResponse)
def delete_case_note(note_id: int, db: Session = Depends(get_db), user: User = Depends(require_admin)):
    return soft_delete(db, active_or_404(db, CaseNote, note_id, "Case note"), user, AuditAction.CASE_NOTE_DELETE, AuditModule.CASE_NOTE)


def create_child_record(db, model, child_id: int, values: dict, user: User, action: AuditAction, module: AuditModule):
    child_or_404(db, child_id)
    record = model(child_id=child_id, **values, created_by=user.id, updated_by=user.id)
    db.add(record); db.flush(); audit_case(db, user, action, module, record.id, new_values=snapshot(record)); db.commit(); db.refresh(record)
    return record


@router.post("/children/{child_id}/counseling-sessions", response_model=CounselingSessionResponse, status_code=201)
def create_counseling(child_id: int, payload: CounselingSessionCreate, db: Session = Depends(get_db), user: User = Depends(can_create_or_update)):
    return create_child_record(db, CounselingSession, child_id, payload.model_dump(), user, AuditAction.COUNSELING_SESSION_CREATE, AuditModule.COUNSELING)


@router.get("/children/{child_id}/counseling-sessions", response_model=list[CounselingSessionResponse])
def list_counseling(child_id: int, db: Session = Depends(get_db), _user: User = Depends(can_operational_read)):
    child_or_404(db, child_id); return db.scalars(select(CounselingSession).where(CounselingSession.child_id == child_id, CounselingSession.deleted_at.is_(None)).order_by(CounselingSession.session_date.desc())).all()


@router.get("/counseling-sessions/{session_id}", response_model=CounselingSessionResponse)
def get_counseling(session_id: int, db: Session = Depends(get_db), _user: User = Depends(can_operational_read)):
    return active_or_404(db, CounselingSession, session_id, "Counseling session")


@router.put("/counseling-sessions/{session_id}", response_model=CounselingSessionResponse)
def update_counseling(session_id: int, payload: CounselingSessionUpdate, db: Session = Depends(get_db), user: User = Depends(can_create_or_update)):
    record = active_or_404(db, CounselingSession, session_id, "Counseling session"); changes = payload.model_dump(exclude_unset=True)
    session_date = changes.get("session_date", record.session_date); next_date = changes.get("next_session_date", record.next_session_date)
    if next_date is not None and next_date < session_date: raise HTTPException(status_code=422, detail="next_session_date cannot be before session_date")
    return update_record(db, record, changes, user, AuditAction.COUNSELING_SESSION_UPDATE, AuditModule.COUNSELING)


@router.delete("/counseling-sessions/{session_id}", response_model=CounselingSessionResponse)
def delete_counseling(session_id: int, db: Session = Depends(get_db), user: User = Depends(require_admin)):
    return soft_delete(db, active_or_404(db, CounselingSession, session_id, "Counseling session"), user, AuditAction.COUNSELING_SESSION_DELETE, AuditModule.COUNSELING)


@router.post("/children/{child_id}/incidents", response_model=IncidentRecordResponse, status_code=201)
def create_incident(child_id: int, payload: IncidentRecordCreate, db: Session = Depends(get_db), user: User = Depends(can_create_or_update)):
    if payload.review_status != IncidentReviewStatus.PENDING:
        raise HTTPException(status_code=409, detail="Create incidents as Pending Review, then use the review workflow")
    return create_child_record(db, IncidentRecord, child_id, payload.model_dump(), user, AuditAction.INCIDENT_CREATE, AuditModule.INCIDENT)


@router.get("/children/{child_id}/incidents", response_model=list[IncidentRecordResponse])
def list_incidents(child_id: int, severity: Severity | None = None, incident_type: IncidentType | None = None, review_status: IncidentReviewStatus | None = None, from_date: date | None = None, to_date: date | None = None, db: Session = Depends(get_db), _user: User = Depends(can_operational_read)):
    child_or_404(db, child_id); stmt = select(IncidentRecord).where(IncidentRecord.child_id == child_id, IncidentRecord.deleted_at.is_(None))
    if severity: stmt = stmt.where(IncidentRecord.severity == severity.value)
    if incident_type: stmt = stmt.where(IncidentRecord.incident_type == incident_type.value)
    if review_status: stmt = stmt.where(IncidentRecord.review_status == review_status.value)
    if from_date: stmt = stmt.where(IncidentRecord.incident_date >= from_date)
    if to_date: stmt = stmt.where(IncidentRecord.incident_date <= to_date)
    return db.scalars(stmt.order_by(IncidentRecord.incident_date.desc())).all()


@router.get("/incidents/{incident_id}", response_model=IncidentRecordResponse)
def get_incident(incident_id: int, db: Session = Depends(get_db), _user: User = Depends(can_operational_read)):
    return active_or_404(db, IncidentRecord, incident_id, "Incident")


@router.put("/incidents/{incident_id}", response_model=IncidentRecordResponse)
def update_incident(incident_id: int, payload: IncidentRecordUpdate, db: Session = Depends(get_db), user: User = Depends(can_create_or_update)):
    return update_record(db, active_or_404(db, IncidentRecord, incident_id, "Incident"), payload.model_dump(exclude_unset=True), user, AuditAction.INCIDENT_UPDATE, AuditModule.INCIDENT)


def transition_incident(db: Session, record: IncidentRecord, target: str, reviewed_at: date, user: User, action: AuditAction):
    if reviewed_at < record.incident_date: raise HTTPException(status_code=422, detail="reviewed_at cannot be before incident_date")
    if record.review_status == "Closed": raise HTTPException(status_code=409, detail="Closed incidents cannot be transitioned")
    if record.review_status == target: raise HTTPException(status_code=409, detail=f"Incident is already {target}")
    return update_record(db, record, {"review_status": target, "reviewed_by": user.id, "reviewed_at": reviewed_at}, user, action, AuditModule.INCIDENT)


@router.post("/incidents/{incident_id}/review", response_model=IncidentRecordResponse)
def review_incident(incident_id: int, payload: IncidentReviewRequest, db: Session = Depends(get_db), user: User = Depends(require_manager)):
    return transition_incident(db, active_or_404(db, IncidentRecord, incident_id, "Incident"), "Reviewed", payload.reviewed_at or date.today(), user, AuditAction.INCIDENT_REVIEW)


@router.post("/incidents/{incident_id}/close", response_model=IncidentRecordResponse)
def close_incident(incident_id: int, payload: IncidentReviewRequest, db: Session = Depends(get_db), user: User = Depends(require_manager)):
    return transition_incident(db, active_or_404(db, IncidentRecord, incident_id, "Incident"), "Closed", payload.reviewed_at or date.today(), user, AuditAction.INCIDENT_CLOSE)


@router.delete("/incidents/{incident_id}", response_model=IncidentRecordResponse)
def delete_incident(incident_id: int, db: Session = Depends(get_db), user: User = Depends(require_admin)):
    return soft_delete(db, active_or_404(db, IncidentRecord, incident_id, "Incident"), user, AuditAction.INCIDENT_DELETE, AuditModule.INCIDENT)


def ensure_active_plan_unique(db: Session, child_id: int, goal_area: str, exclude_id: int | None = None):
    stmt = select(CarePlan.id).where(CarePlan.child_id == child_id, CarePlan.goal_area == goal_area, CarePlan.status == "Active", CarePlan.deleted_at.is_(None))
    if exclude_id is not None: stmt = stmt.where(CarePlan.id != exclude_id)
    if db.scalar(stmt.limit(1)): raise HTTPException(status_code=409, detail="Active care plan already exists for this goal area")


@router.post("/children/{child_id}/care-plans", response_model=CarePlanResponse, status_code=201)
def create_care_plan(child_id: int, payload: CarePlanCreate, db: Session = Depends(get_db), user: User = Depends(can_create_or_update)):
    child_or_404(db, child_id); validate_profile_link(db, payload.case_profile_id, child_id)
    if payload.status.value == "Active": ensure_active_plan_unique(db, child_id, payload.goal_area.value)
    record = CarePlan(child_id=child_id, **payload.model_dump(), created_by=user.id, updated_by=user.id); db.add(record)
    try:
        db.flush(); audit_case(db, user, AuditAction.CARE_PLAN_CREATE, AuditModule.CARE_PLAN, record.id, new_values=snapshot(record)); db.commit()
    except IntegrityError as exc:
        db.rollback(); raise HTTPException(status_code=409, detail="Active care plan already exists for this goal area") from exc
    db.refresh(record); return record


@router.get("/children/{child_id}/care-plans", response_model=list[CarePlanResponse])
def list_care_plans(child_id: int, db: Session = Depends(get_db), _user: User = Depends(can_operational_read)):
    child_or_404(db, child_id); return db.scalars(select(CarePlan).where(CarePlan.child_id == child_id, CarePlan.deleted_at.is_(None)).order_by(CarePlan.plan_start_date.desc())).all()


@router.get("/care-plans/{plan_id}", response_model=CarePlanResponse)
def get_care_plan(plan_id: int, db: Session = Depends(get_db), _user: User = Depends(can_operational_read)):
    return active_or_404(db, CarePlan, plan_id, "Care plan")


@router.put("/care-plans/{plan_id}", response_model=CarePlanResponse)
def update_care_plan(plan_id: int, payload: CarePlanUpdate, db: Session = Depends(get_db), user: User = Depends(can_create_or_update)):
    record = active_or_404(db, CarePlan, plan_id, "Care plan"); changes = payload.model_dump(exclude_unset=True)
    start = changes.get("plan_start_date", record.plan_start_date); end = changes.get("plan_end_date", record.plan_end_date)
    if end is not None and end < start: raise HTTPException(status_code=422, detail="plan_end_date cannot be before plan_start_date")
    goal = changes.get("goal_area", record.goal_area); target_status = changes.get("status", record.status)
    if target_status in {"Completed", "Cancelled"} and target_status != record.status:
        raise HTTPException(status_code=409, detail="Use the dedicated complete or cancel endpoint")
    if target_status == "Active" and (record.status != "Active" or goal != record.goal_area): ensure_active_plan_unique(db, record.child_id, goal, record.id)
    return update_record(db, record, changes, user, AuditAction.CARE_PLAN_UPDATE, AuditModule.CARE_PLAN)


def transition_plan(db: Session, plan_id: int, target: str, user: User, action: AuditAction):
    record = active_or_404(db, CarePlan, plan_id, "Care plan")
    if record.status == target: raise HTTPException(status_code=409, detail=f"Care plan is already {target}")
    return update_record(db, record, {"status": target}, user, action, AuditModule.CARE_PLAN)


@router.post("/care-plans/{plan_id}/complete", response_model=CarePlanResponse)
def complete_care_plan(plan_id: int, db: Session = Depends(get_db), user: User = Depends(can_create_or_update)):
    return transition_plan(db, plan_id, "Completed", user, AuditAction.CARE_PLAN_COMPLETE)


@router.post("/care-plans/{plan_id}/cancel", response_model=CarePlanResponse)
def cancel_care_plan(plan_id: int, db: Session = Depends(get_db), user: User = Depends(can_create_or_update)):
    return transition_plan(db, plan_id, "Cancelled", user, AuditAction.CARE_PLAN_CANCEL)


@router.delete("/care-plans/{plan_id}", response_model=CarePlanResponse)
def delete_care_plan(plan_id: int, db: Session = Depends(get_db), user: User = Depends(require_admin)):
    return soft_delete(db, active_or_404(db, CarePlan, plan_id, "Care plan"), user, AuditAction.CARE_PLAN_DELETE, AuditModule.CARE_PLAN)


@router.post("/children/{child_id}/case-reviews", response_model=CaseReviewResponse, status_code=201)
def create_case_review(child_id: int, payload: CaseReviewCreate, db: Session = Depends(get_db), user: User = Depends(can_create_or_update)):
    child_or_404(db, child_id); validate_profile_link(db, payload.case_profile_id, child_id)
    return create_child_record(db, CaseReview, child_id, payload.model_dump(), user, AuditAction.CASE_REVIEW_CREATE, AuditModule.CASE_REVIEW)


@router.get("/children/{child_id}/case-reviews", response_model=list[CaseReviewResponse])
def list_case_reviews(child_id: int, db: Session = Depends(get_db), _user: User = Depends(can_operational_read)):
    child_or_404(db, child_id); return db.scalars(select(CaseReview).where(CaseReview.child_id == child_id, CaseReview.deleted_at.is_(None)).order_by(CaseReview.review_date.desc())).all()


@router.get("/case-reviews/{review_id}", response_model=CaseReviewResponse)
def get_case_review(review_id: int, db: Session = Depends(get_db), _user: User = Depends(can_operational_read)):
    return active_or_404(db, CaseReview, review_id, "Case review")


@router.put("/case-reviews/{review_id}", response_model=CaseReviewResponse)
def update_case_review(review_id: int, payload: CaseReviewUpdate, db: Session = Depends(get_db), user: User = Depends(can_create_or_update)):
    record = active_or_404(db, CaseReview, review_id, "Case review"); changes = payload.model_dump(exclude_unset=True)
    review_date = changes.get("review_date", record.review_date); next_date = changes.get("next_review_date", record.next_review_date)
    if next_date is not None and next_date < review_date: raise HTTPException(status_code=422, detail="next_review_date cannot be before review_date")
    return update_record(db, record, changes, user, AuditAction.CASE_REVIEW_UPDATE, AuditModule.CASE_REVIEW)


@router.delete("/case-reviews/{review_id}", response_model=CaseReviewResponse)
def delete_case_review(review_id: int, db: Session = Depends(get_db), user: User = Depends(require_admin)):
    return soft_delete(db, active_or_404(db, CaseReview, review_id, "Case review"), user, AuditAction.CASE_REVIEW_DELETE, AuditModule.CASE_REVIEW)


def active_profiles(): return ChildCaseProfile.deleted_at.is_(None)
def active_notes(): return CaseNote.deleted_at.is_(None)


@router.get("/reports/case-profiles", response_model=list[ChildCaseProfileResponse], tags=["Case Management Reports"])
def report_profiles(db: Session = Depends(get_db), _user: User = Depends(can_operational_read)): return db.scalars(select(ChildCaseProfile).where(active_profiles()).order_by(ChildCaseProfile.case_number)).all()
@router.get("/reports/open-cases", response_model=list[ChildCaseProfileResponse], tags=["Case Management Reports"])
def report_open(db: Session = Depends(get_db), _user: User = Depends(can_operational_read)): return db.scalars(select(ChildCaseProfile).where(active_profiles(), ChildCaseProfile.case_status.in_(["Open", "Under Review"]))).all()
@router.get("/reports/closed-cases", response_model=list[ChildCaseProfileResponse], tags=["Case Management Reports"])
def report_closed(db: Session = Depends(get_db), _user: User = Depends(can_operational_read)): return db.scalars(select(ChildCaseProfile).where(active_profiles(), ChildCaseProfile.case_status == "Closed")).all()
@router.get("/reports/high-risk-children", response_model=list[ChildCaseProfileResponse], tags=["Case Management Reports"])
def report_high_risk(db: Session = Depends(get_db), _user: User = Depends(can_operational_read)): return db.scalars(select(ChildCaseProfile).where(active_profiles(), ChildCaseProfile.risk_level == "High")).all()
@router.get("/reports/critical-risk-children", response_model=list[ChildCaseProfileResponse], tags=["Case Management Reports"])
def report_critical_risk(db: Session = Depends(get_db), _user: User = Depends(can_operational_read)): return db.scalars(select(ChildCaseProfile).where(active_profiles(), ChildCaseProfile.risk_level == "Critical")).all()


@router.get("/reports/pending-follow-ups", response_model=list[CaseNoteResponse], tags=["Case Management Reports"])
def report_follow_ups(db: Session = Depends(get_db), user: User = Depends(can_operational_read)):
    return db.scalars(select(CaseNote).where(active_notes(), CaseNote.follow_up_required.is_(True), CaseNote.follow_up_date <= date.today(), CaseNote.visibility.in_(allowed_note_visibilities(user))).order_by(CaseNote.follow_up_date)).all()


def within_30(column):
    return column.between(date.today(), date.today() + timedelta(days=30))


@router.get("/reports/upcoming-case-reviews", response_model=list[CaseReviewResponse], tags=["Case Management Reports"])
def report_upcoming_reviews(db: Session = Depends(get_db), _user: User = Depends(can_operational_read)):
    return db.scalars(select(CaseReview).where(CaseReview.deleted_at.is_(None), or_(within_30(CaseReview.next_review_date), (CaseReview.status == "Pending") & within_30(CaseReview.review_date))).order_by(CaseReview.review_date)).all()
@router.get("/reports/upcoming-counseling-sessions", response_model=list[CounselingSessionResponse], tags=["Case Management Reports"])
def report_upcoming_counseling(db: Session = Depends(get_db), _user: User = Depends(can_operational_read)):
    return db.scalars(select(CounselingSession).where(CounselingSession.deleted_at.is_(None), or_(within_30(CounselingSession.next_session_date), (CounselingSession.status == "Scheduled") & within_30(CounselingSession.session_date))).order_by(CounselingSession.session_date)).all()
@router.get("/reports/critical-incidents", response_model=list[IncidentRecordResponse], tags=["Case Management Reports"])
def report_critical_incidents(db: Session = Depends(get_db), _user: User = Depends(can_operational_read)): return db.scalars(select(IncidentRecord).where(IncidentRecord.deleted_at.is_(None), IncidentRecord.severity == "Critical").order_by(IncidentRecord.incident_date.desc())).all()
@router.get("/reports/pending-incident-reviews", response_model=list[IncidentRecordResponse], tags=["Case Management Reports"])
def report_pending_incidents(db: Session = Depends(get_db), _user: User = Depends(can_operational_read)): return db.scalars(select(IncidentRecord).where(IncidentRecord.deleted_at.is_(None), IncidentRecord.review_status == "Pending Review").order_by(IncidentRecord.incident_date)).all()
@router.get("/reports/active-care-plans", response_model=list[CarePlanResponse], tags=["Case Management Reports"])
def report_active_plans(db: Session = Depends(get_db), _user: User = Depends(can_operational_read)): return db.scalars(select(CarePlan).where(CarePlan.deleted_at.is_(None), CarePlan.status == "Active")).all()
@router.get("/reports/completed-care-plans", response_model=list[CarePlanResponse], tags=["Case Management Reports"])
def report_completed_plans(db: Session = Depends(get_db), _user: User = Depends(can_operational_read)): return db.scalars(select(CarePlan).where(CarePlan.deleted_at.is_(None), CarePlan.status == "Completed")).all()


@router.get("/dashboard/case-management", response_model=CaseDashboardResponse, tags=["Case Management Dashboard"])
def case_dashboard(db: Session = Depends(get_db), user: User = Depends(can_operational_read)):
    count = lambda stmt: db.scalar(stmt) or 0
    profiles = select(func.count()).select_from(ChildCaseProfile).where(active_profiles())
    profile_exists = select(ChildCaseProfile.id).where(ChildCaseProfile.child_id == Child.id, active_profiles())
    return CaseDashboardResponse(
        total_case_profiles=count(profiles),
        open_cases=count(select(func.count()).select_from(ChildCaseProfile).where(active_profiles(), ChildCaseProfile.case_status.in_(["Open", "Under Review"]))),
        closed_cases=count(select(func.count()).select_from(ChildCaseProfile).where(active_profiles(), ChildCaseProfile.case_status == "Closed")),
        high_risk_children=count(select(func.count()).select_from(ChildCaseProfile).where(active_profiles(), ChildCaseProfile.risk_level == "High")),
        critical_risk_children=count(select(func.count()).select_from(ChildCaseProfile).where(active_profiles(), ChildCaseProfile.risk_level == "Critical")),
        pending_follow_ups=count(select(func.count()).select_from(CaseNote).where(active_notes(), CaseNote.follow_up_required.is_(True), CaseNote.follow_up_date <= date.today(), CaseNote.visibility.in_(allowed_note_visibilities(user)))),
        upcoming_case_reviews=count(select(func.count()).select_from(CaseReview).where(CaseReview.deleted_at.is_(None), or_(within_30(CaseReview.next_review_date), (CaseReview.status == "Pending") & within_30(CaseReview.review_date)))),
        upcoming_counseling_sessions=count(select(func.count()).select_from(CounselingSession).where(CounselingSession.deleted_at.is_(None), or_(within_30(CounselingSession.next_session_date), (CounselingSession.status == "Scheduled") & within_30(CounselingSession.session_date)))),
        critical_incidents=count(select(func.count()).select_from(IncidentRecord).where(IncidentRecord.deleted_at.is_(None), IncidentRecord.severity == "Critical", IncidentRecord.review_status != "Closed")),
        pending_incident_reviews=count(select(func.count()).select_from(IncidentRecord).where(IncidentRecord.deleted_at.is_(None), IncidentRecord.review_status == "Pending Review")),
        active_care_plans=count(select(func.count()).select_from(CarePlan).where(CarePlan.deleted_at.is_(None), CarePlan.status == "Active")),
        children_without_case_profile=count(select(func.count()).select_from(Child).where(not_(profile_exists.exists()))),
    )
