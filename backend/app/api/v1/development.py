from datetime import UTC, date, datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import extract, func, select
from sqlalchemy.orm import Session, selectinload

from app.core.deps import get_db, require_permission
from app.models.child import Child
from app.models.development import ChildBehaviorSupportPlan, ChildBehaviorSupportPlanNote, ChildDevelopmentAISummary, ChildDevelopmentObservation, ChildDevelopmentObservationResponse, DevelopmentIndicator
from app.models.user import User
from app.schemas.development import BehaviorSupportPlanCreate, BehaviorSupportPlanNoteCreate, BehaviorSupportPlanNoteResponse, BehaviorSupportPlanNoteUpdate, BehaviorSupportPlanResponse, BehaviorSupportPlanUpdate, DevelopmentAISummaryResponse, DevelopmentAISummaryReviewRequest, DevelopmentAISummaryUpdate, DevelopmentIndicatorCreate, DevelopmentIndicatorResponse, DevelopmentIndicatorUpdate, DevelopmentSummary, ObservationCreate, ObservationResponse, ObservationReviewRequest, ObservationUpdate
from app.services.audit import AuditAction, AuditModule, add_audit_log
from app.services.development_service import clean_observation, create_observation, development_summary, missing_monthly_rows, seed_development_indicators, update_observation
from app.services.development_ai_service import SAFE_FOOTER, clean_ai_summary, generate_ai_summary, summary_row
from app.services.behavior_support_service import PLAN_FOOTER, create_plan, generate_support_plan, plan_row, safe_text as support_safe_text, set_plan_status
from app.services.excel_service import build_excel_report
from app.services.organization_profile_service import report_branding
from app.services.pdf_service import build_pdf_report

router = APIRouter(tags=["Child Development Profile"])


def observation_query():
    return select(ChildDevelopmentObservation).options(selectinload(ChildDevelopmentObservation.responses).selectinload(ChildDevelopmentObservationResponse.indicator))


def observation_or_404(db: Session, observation_id: int) -> ChildDevelopmentObservation:
    item = db.scalar(observation_query().where(ChildDevelopmentObservation.id == observation_id))
    if item is None:
        raise HTTPException(404, "Development observation not found")
    return item


def ai_summary_or_404(db: Session, summary_id: int) -> ChildDevelopmentAISummary:
    item = db.get(ChildDevelopmentAISummary, summary_id)
    if item is None:
        raise HTTPException(404, "Development AI summary not found")
    return item


def support_plan_or_404(db: Session, plan_id: int) -> ChildBehaviorSupportPlan:
    item = db.get(ChildBehaviorSupportPlan, plan_id)
    if item is None:
        raise HTTPException(404, "Behavior support plan not found")
    return item


def support_note_or_404(db: Session, note_id: int) -> ChildBehaviorSupportPlanNote:
    item = db.get(ChildBehaviorSupportPlanNote, note_id)
    if item is None:
        raise HTTPException(404, "Behavior support plan note not found")
    return item


def ai_response(db: Session, item: ChildDevelopmentAISummary, user: User) -> dict:
    child = db.get(Child, item.child_id)
    return summary_row(clean_ai_summary(item, user), child)


def obs_response(item: ChildDevelopmentObservation, user: User) -> ChildDevelopmentObservation:
    return clean_observation(item, user)


def child_base_query(child_id: int | None = None, district: str | None = None):
    query = select(Child).order_by(Child.full_name)
    if child_id:
        query = query.where(Child.id == child_id)
    if district:
        query = query.where(Child.district.ilike(f"%{district}%"))
    return query


def talent_rows(db: Session, user: User, month: int | None = None, year: int | None = None, child_id: int | None = None, district: str | None = None) -> list[dict]:
    rows = []
    for child in db.scalars(child_base_query(child_id=child_id, district=district)).all():
        summary = development_summary(db, child.id, user)
        latest_date = summary["latest_observation_date"]
        if month and year and latest_date and (latest_date.month != month or latest_date.year != year):
            continue
        rows.append(
            {
                "id": child.id,
                "child_id": child.id,
                "child_code": child.child_id,
                "full_name": child.full_name,
                "possible_areas_of_interest": summary["possible_areas_of_interest"],
                "positive_strengths": summary["positive_strengths"],
                "support_needs": summary["support_needs"],
                "last_observation_date": latest_date,
            }
        )
    return rows


@router.get("/development-indicators", response_model=list[DevelopmentIndicatorResponse])
def list_indicators(include_inactive: bool = False, db: Session = Depends(get_db), _user: User = Depends(require_permission("development.indicators.view"))):
    seed_development_indicators(db)
    query = select(DevelopmentIndicator).order_by(DevelopmentIndicator.sort_order, DevelopmentIndicator.indicator_name)
    if not include_inactive:
        query = query.where(DevelopmentIndicator.is_active.is_(True))
    db.commit()
    return db.scalars(query).all()


@router.post("/development-indicators", response_model=DevelopmentIndicatorResponse, status_code=201)
def create_indicator(payload: DevelopmentIndicatorCreate, db: Session = Depends(get_db), user: User = Depends(require_permission("development.indicators.manage"))):
    if db.scalar(select(DevelopmentIndicator.id).where(DevelopmentIndicator.indicator_code == payload.indicator_code)):
        raise HTTPException(409, "Indicator code already exists")
    item = DevelopmentIndicator(**payload.model_dump())
    db.add(item); db.flush()
    add_audit_log(db, user_id=user.id, action=AuditAction.DEVELOPMENT_INDICATOR_CREATED, module=AuditModule.CHILD_DEVELOPMENT, record_id=item.id, new_values=payload.model_dump())
    db.commit(); db.refresh(item)
    return item


@router.put("/development-indicators/{indicator_id}", response_model=DevelopmentIndicatorResponse)
def update_indicator(indicator_id: int, payload: DevelopmentIndicatorUpdate, db: Session = Depends(get_db), user: User = Depends(require_permission("development.indicators.manage"))):
    item = db.get(DevelopmentIndicator, indicator_id)
    if item is None:
        raise HTTPException(404, "Development indicator not found")
    old = {"indicator_name": item.indicator_name, "description": item.description, "options_json": item.options_json}
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(item, key, value)
    add_audit_log(db, user_id=user.id, action=AuditAction.DEVELOPMENT_INDICATOR_UPDATED, module=AuditModule.CHILD_DEVELOPMENT, record_id=item.id, old_values=old, new_values=payload.model_dump(exclude_unset=True))
    db.commit(); db.refresh(item)
    return item


@router.post("/development-indicators/{indicator_id}/activate", response_model=DevelopmentIndicatorResponse)
def activate_indicator(indicator_id: int, db: Session = Depends(get_db), user: User = Depends(require_permission("development.indicators.manage"))):
    item = db.get(DevelopmentIndicator, indicator_id)
    if item is None:
        raise HTTPException(404, "Development indicator not found")
    item.is_active = True
    add_audit_log(db, user_id=user.id, action=AuditAction.DEVELOPMENT_INDICATOR_ACTIVATED, module=AuditModule.CHILD_DEVELOPMENT, record_id=item.id)
    db.commit(); return item


@router.post("/development-indicators/{indicator_id}/deactivate", response_model=DevelopmentIndicatorResponse)
def deactivate_indicator(indicator_id: int, db: Session = Depends(get_db), user: User = Depends(require_permission("development.indicators.manage"))):
    item = db.get(DevelopmentIndicator, indicator_id)
    if item is None:
        raise HTTPException(404, "Development indicator not found")
    item.is_active = False
    add_audit_log(db, user_id=user.id, action=AuditAction.DEVELOPMENT_INDICATOR_DEACTIVATED, module=AuditModule.CHILD_DEVELOPMENT, record_id=item.id)
    db.commit(); return item


@router.get("/child-development-observations", response_model=list[ObservationResponse])
def list_observations(child_id: int | None = None, status: str | None = None, db: Session = Depends(get_db), user: User = Depends(require_permission("development.view"))):
    query = observation_query().order_by(ChildDevelopmentObservation.observation_date.desc(), ChildDevelopmentObservation.id.desc())
    if child_id:
        query = query.where(ChildDevelopmentObservation.child_id == child_id)
    if status:
        query = query.where(ChildDevelopmentObservation.review_status == status)
    return [obs_response(item, user) for item in db.scalars(query).all()]


@router.post("/child-development-observations", response_model=ObservationResponse, status_code=201)
def create_development_observation(payload: ObservationCreate, db: Session = Depends(get_db), user: User = Depends(require_permission("development.create"))):
    item = create_observation(db, payload, user)
    add_audit_log(db, user_id=user.id, action=AuditAction.CHILD_DEVELOPMENT_OBSERVATION_CREATED, module=AuditModule.CHILD_DEVELOPMENT, record_id=item.id, new_values={"child_id": item.child_id, "frequency": item.observation_frequency, "urgent_flag": item.urgent_flag})
    db.commit(); db.refresh(item)
    return obs_response(item, user)


@router.get("/child-development-observations/{observation_id}", response_model=ObservationResponse)
def get_observation(observation_id: int, db: Session = Depends(get_db), user: User = Depends(require_permission("development.view"))):
    return obs_response(observation_or_404(db, observation_id), user)


@router.put("/child-development-observations/{observation_id}", response_model=ObservationResponse)
def update_development_observation(observation_id: int, payload: ObservationUpdate, db: Session = Depends(get_db), user: User = Depends(require_permission("development.update"))):
    item = update_observation(db, observation_or_404(db, observation_id), payload, user)
    add_audit_log(db, user_id=user.id, action=AuditAction.CHILD_DEVELOPMENT_OBSERVATION_UPDATED, module=AuditModule.CHILD_DEVELOPMENT, record_id=item.id, new_values={"urgent_flag": item.urgent_flag})
    db.commit(); db.refresh(item)
    return obs_response(item, user)


@router.delete("/child-development-observations/{observation_id}")
def archive_observation_delete_alias(observation_id: int, db: Session = Depends(get_db), user: User = Depends(require_permission("development.delete"))):
    return archive_observation(observation_id, db, user)


@router.post("/child-development-observations/{observation_id}/submit", response_model=ObservationResponse)
def submit_observation(observation_id: int, db: Session = Depends(get_db), user: User = Depends(require_permission("development.submit"))):
    item = observation_or_404(db, observation_id)
    if item.review_status not in {"Draft", "Needs Follow-up"}:
        raise HTTPException(409, "Only draft or follow-up observations can be submitted")
    item.review_status = "Submitted"; item.submitted_at = datetime.now(UTC); item.updated_by_user_id = user.id
    add_audit_log(db, user_id=user.id, action=AuditAction.CHILD_DEVELOPMENT_OBSERVATION_SUBMITTED, module=AuditModule.CHILD_DEVELOPMENT, record_id=item.id)
    db.commit(); return obs_response(item, user)


@router.post("/child-development-observations/{observation_id}/review", response_model=ObservationResponse)
def review_observation(observation_id: int, payload: ObservationReviewRequest, db: Session = Depends(get_db), user: User = Depends(require_permission("development.review"))):
    item = observation_or_404(db, observation_id)
    item.review_status = payload.review_status; item.reviewed_by_user_id = user.id; item.reviewed_at = datetime.now(UTC); item.updated_by_user_id = user.id
    if payload.recommended_support is not None:
        item.recommended_support = payload.recommended_support
    if payload.next_review_date is not None:
        item.next_review_date = payload.next_review_date
    add_audit_log(db, user_id=user.id, action=AuditAction.CHILD_DEVELOPMENT_OBSERVATION_REVIEWED, module=AuditModule.CHILD_DEVELOPMENT, record_id=item.id, new_values=payload.model_dump())
    db.commit(); return obs_response(item, user)


@router.post("/child-development-observations/{observation_id}/close", response_model=ObservationResponse)
def close_observation(observation_id: int, db: Session = Depends(get_db), user: User = Depends(require_permission("development.close"))):
    item = observation_or_404(db, observation_id)
    item.review_status = "Closed"; item.closed_at = datetime.now(UTC); item.updated_by_user_id = user.id
    add_audit_log(db, user_id=user.id, action=AuditAction.CHILD_DEVELOPMENT_OBSERVATION_CLOSED, module=AuditModule.CHILD_DEVELOPMENT, record_id=item.id)
    db.commit(); return obs_response(item, user)


@router.post("/child-development-observations/{observation_id}/archive", response_model=ObservationResponse)
def archive_observation(observation_id: int, db: Session = Depends(get_db), user: User = Depends(require_permission("development.delete"))):
    item = observation_or_404(db, observation_id)
    item.review_status = "Archived"; item.updated_by_user_id = user.id
    add_audit_log(db, user_id=user.id, action=AuditAction.CHILD_DEVELOPMENT_OBSERVATION_ARCHIVED, module=AuditModule.CHILD_DEVELOPMENT, record_id=item.id)
    db.commit(); return obs_response(item, user)


@router.get("/children/{child_id}/development-observations", response_model=list[ObservationResponse])
def child_observations(child_id: int, db: Session = Depends(get_db), user: User = Depends(require_permission("development.view"))):
    return [obs_response(item, user) for item in db.scalars(observation_query().where(ChildDevelopmentObservation.child_id == child_id).order_by(ChildDevelopmentObservation.observation_date.desc())).all()]


@router.get("/children/{child_id}/development-summary", response_model=DevelopmentSummary)
def child_development_summary(child_id: int, db: Session = Depends(get_db), user: User = Depends(require_permission("development.view"))):
    if db.get(Child, child_id) is None:
        raise HTTPException(404, "Child not found")
    return development_summary(db, child_id, user)


@router.get("/children/{child_id}/development-profile")
def child_development_profile(child_id: int, db: Session = Depends(get_db), user: User = Depends(require_permission("development.view"))):
    child = db.get(Child, child_id)
    if child is None:
        raise HTTPException(404, "Child not found")
    return {"child": {"id": child.id, "child_id": child.child_id, "full_name": child.full_name, "gender": child.gender, "district": child.district, "status": child.status}, "summary": development_summary(db, child_id, user), "observations": child_observations(child_id, db, user)}


@router.get("/children/{child_id}/development-ai-summaries", response_model=list[DevelopmentAISummaryResponse])
def child_ai_summaries(child_id: int, db: Session = Depends(get_db), user: User = Depends(require_permission("development.ai_summary.view"))):
    if db.get(Child, child_id) is None:
        raise HTTPException(404, "Child not found")
    rows = db.scalars(select(ChildDevelopmentAISummary).where(ChildDevelopmentAISummary.child_id == child_id, ChildDevelopmentAISummary.approval_status != "Archived").order_by(ChildDevelopmentAISummary.generated_at.desc(), ChildDevelopmentAISummary.id.desc())).all()
    if not any(role.name in {"Admin", "Manager", "Counselor"} for role in user.roles):
        rows = [row for row in rows if row.approval_status == "Approved"]
    return [ai_response(db, row, user) for row in rows]


@router.get("/children/{child_id}/development-ai-summaries/latest", response_model=DevelopmentAISummaryResponse)
def latest_child_ai_summary(child_id: int, db: Session = Depends(get_db), user: User = Depends(require_permission("development.ai_summary.view"))):
    if db.get(Child, child_id) is None:
        raise HTTPException(404, "Child not found")
    query = select(ChildDevelopmentAISummary).where(ChildDevelopmentAISummary.child_id == child_id, ChildDevelopmentAISummary.approval_status != "Archived")
    if not any(role.name in {"Admin", "Manager", "Counselor"} for role in user.roles):
        query = query.where(ChildDevelopmentAISummary.approval_status == "Approved")
    item = db.scalar(query.order_by(ChildDevelopmentAISummary.generated_at.desc(), ChildDevelopmentAISummary.id.desc()).limit(1))
    if item is None:
        raise HTTPException(404, "Development AI summary not found")
    return ai_response(db, item, user)


@router.post("/children/{child_id}/development-ai-summaries/generate", response_model=DevelopmentAISummaryResponse, status_code=201)
def generate_child_ai_summary(child_id: int, month: int | None = Query(default=None, ge=1, le=12), year: int | None = Query(default=None, ge=2000, le=2100), db: Session = Depends(get_db), user: User = Depends(require_permission("development.ai_summary.generate"))):
    item = generate_ai_summary(db, child_id, user, month=month, year=year)
    add_audit_log(db, user_id=user.id, action=AuditAction.CHILD_DEVELOPMENT_AI_SUMMARY_GENERATED, module=AuditModule.CHILD_DEVELOPMENT, record_id=item.id, new_values={"child_id": child_id, "status": item.approval_status})
    db.commit(); db.refresh(item)
    return ai_response(db, item, user)


@router.get("/development-ai-summaries/{summary_id}", response_model=DevelopmentAISummaryResponse)
def get_ai_summary(summary_id: int, db: Session = Depends(get_db), user: User = Depends(require_permission("development.ai_summary.view"))):
    item = ai_summary_or_404(db, summary_id)
    if item.approval_status != "Approved" and not any(role.name in {"Admin", "Manager", "Counselor"} for role in user.roles):
        raise HTTPException(403, "Approved summary access only")
    return ai_response(db, item, user)


@router.put("/development-ai-summaries/{summary_id}", response_model=DevelopmentAISummaryResponse)
def update_ai_summary(summary_id: int, payload: DevelopmentAISummaryUpdate, db: Session = Depends(get_db), user: User = Depends(require_permission("development.ai_summary.update"))):
    item = ai_summary_or_404(db, summary_id)
    if item.approval_status in {"Approved", "Archived"}:
        raise HTTPException(409, "Approved or archived summaries cannot be edited")
    old = {"approval_status": item.approval_status, "trend_status": item.trend_status, "attention_level": item.attention_level}
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(item, key, value)
    add_audit_log(db, user_id=user.id, action=AuditAction.CHILD_DEVELOPMENT_AI_SUMMARY_UPDATED, module=AuditModule.CHILD_DEVELOPMENT, record_id=item.id, old_values=old, new_values=payload.model_dump(exclude_unset=True))
    db.commit(); db.refresh(item)
    return ai_response(db, item, user)


@router.post("/development-ai-summaries/{summary_id}/review", response_model=DevelopmentAISummaryResponse)
def review_ai_summary(summary_id: int, payload: DevelopmentAISummaryReviewRequest | None = None, db: Session = Depends(get_db), user: User = Depends(require_permission("development.ai_summary.review"))):
    item = ai_summary_or_404(db, summary_id)
    item.approval_status = "Reviewed"; item.reviewed_by_user_id = user.id; item.reviewed_at = datetime.now(UTC)
    if payload and payload.internal_notes is not None:
        item.internal_notes = payload.internal_notes
    add_audit_log(db, user_id=user.id, action=AuditAction.CHILD_DEVELOPMENT_AI_SUMMARY_REVIEWED, module=AuditModule.CHILD_DEVELOPMENT, record_id=item.id)
    db.commit(); db.refresh(item)
    return ai_response(db, item, user)


@router.post("/development-ai-summaries/{summary_id}/approve", response_model=DevelopmentAISummaryResponse)
def approve_ai_summary(summary_id: int, db: Session = Depends(get_db), user: User = Depends(require_permission("development.ai_summary.approve"))):
    item = ai_summary_or_404(db, summary_id)
    if item.approval_status not in {"Generated", "Reviewed"}:
        raise HTTPException(409, "Only generated or reviewed summaries can be approved")
    item.approval_status = "Approved"; item.approved_by_user_id = user.id; item.approved_at = datetime.now(UTC)
    add_audit_log(db, user_id=user.id, action=AuditAction.CHILD_DEVELOPMENT_AI_SUMMARY_APPROVED, module=AuditModule.CHILD_DEVELOPMENT, record_id=item.id)
    db.commit(); db.refresh(item)
    return ai_response(db, item, user)


@router.post("/development-ai-summaries/{summary_id}/reject", response_model=DevelopmentAISummaryResponse)
def reject_ai_summary(summary_id: int, payload: DevelopmentAISummaryReviewRequest | None = None, db: Session = Depends(get_db), user: User = Depends(require_permission("development.ai_summary.reject"))):
    item = ai_summary_or_404(db, summary_id)
    item.approval_status = "Rejected"; item.reviewed_by_user_id = user.id; item.reviewed_at = datetime.now(UTC)
    if payload and payload.internal_notes is not None:
        item.internal_notes = payload.internal_notes
    add_audit_log(db, user_id=user.id, action=AuditAction.CHILD_DEVELOPMENT_AI_SUMMARY_REJECTED, module=AuditModule.CHILD_DEVELOPMENT, record_id=item.id)
    db.commit(); db.refresh(item)
    return ai_response(db, item, user)


@router.delete("/development-ai-summaries/{summary_id}", response_model=DevelopmentAISummaryResponse)
def archive_ai_summary(summary_id: int, db: Session = Depends(get_db), user: User = Depends(require_permission("development.ai_summary.delete"))):
    item = ai_summary_or_404(db, summary_id)
    item.approval_status = "Archived"
    add_audit_log(db, user_id=user.id, action=AuditAction.CHILD_DEVELOPMENT_AI_SUMMARY_ARCHIVED, module=AuditModule.CHILD_DEVELOPMENT, record_id=item.id)
    db.commit(); db.refresh(item)
    return ai_response(db, item, user)


@router.get("/children/{child_id}/behavior-support-plans", response_model=list[BehaviorSupportPlanResponse])
def child_behavior_support_plans(child_id: int, db: Session = Depends(get_db), user: User = Depends(require_permission("development.support_plan.view"))):
    if db.get(Child, child_id) is None:
        raise HTTPException(404, "Child not found")
    query = select(ChildBehaviorSupportPlan).where(ChildBehaviorSupportPlan.child_id == child_id, ChildBehaviorSupportPlan.plan_status != "Archived").order_by(ChildBehaviorSupportPlan.created_at.desc(), ChildBehaviorSupportPlan.id.desc())
    rows = db.scalars(query).all()
    if not any(role.name in {"Admin", "Manager", "Counselor", "Warden"} for role in user.roles):
        rows = [row for row in rows if row.plan_status == "Active"]
    return [plan_row(db, row, user) for row in rows]


@router.post("/children/{child_id}/behavior-support-plans", response_model=BehaviorSupportPlanResponse, status_code=201)
def create_behavior_support_plan(child_id: int, payload: BehaviorSupportPlanCreate, db: Session = Depends(get_db), user: User = Depends(require_permission("development.support_plan.create"))):
    item = create_plan(db, child_id, payload, user)
    add_audit_log(db, user_id=user.id, action=AuditAction.BEHAVIOR_SUPPORT_PLAN_CREATED, module=AuditModule.CHILD_DEVELOPMENT, record_id=item.id, new_values={"child_id": child_id, "plan_code": item.plan_code})
    db.commit(); db.refresh(item)
    return plan_row(db, item, user)


@router.post("/children/{child_id}/behavior-support-plans/generate", response_model=BehaviorSupportPlanResponse, status_code=201)
def generate_behavior_support_plan(child_id: int, db: Session = Depends(get_db), user: User = Depends(require_permission("development.support_plan.generate"))):
    item = generate_support_plan(db, child_id, user)
    add_audit_log(db, user_id=user.id, action=AuditAction.BEHAVIOR_SUPPORT_PLAN_GENERATED, module=AuditModule.CHILD_DEVELOPMENT, record_id=item.id, new_values={"child_id": child_id, "plan_code": item.plan_code})
    db.commit(); db.refresh(item)
    return plan_row(db, item, user)


@router.get("/behavior-support-plans/{plan_id}", response_model=BehaviorSupportPlanResponse)
def get_behavior_support_plan(plan_id: int, db: Session = Depends(get_db), user: User = Depends(require_permission("development.support_plan.view"))):
    item = support_plan_or_404(db, plan_id)
    if item.plan_status != "Active" and not any(role.name in {"Admin", "Manager", "Counselor", "Warden"} for role in user.roles):
        raise HTTPException(403, "Active support plan access only")
    return plan_row(db, item, user)


@router.put("/behavior-support-plans/{plan_id}", response_model=BehaviorSupportPlanResponse)
def update_behavior_support_plan(plan_id: int, payload: BehaviorSupportPlanUpdate, db: Session = Depends(get_db), user: User = Depends(require_permission("development.support_plan.update"))):
    item = support_plan_or_404(db, plan_id)
    if item.plan_status in {"Closed", "Cancelled", "Archived"}:
        raise HTTPException(409, "Closed, cancelled, or archived plans cannot be edited")
    old = {"plan_status": item.plan_status, "priority_level": item.priority_level}
    for key, value in payload.model_dump(exclude_unset=True).items():
        if isinstance(value, str):
            value = support_safe_text(value)
        setattr(item, key, value)
    item.updated_by_user_id = user.id
    add_audit_log(db, user_id=user.id, action=AuditAction.BEHAVIOR_SUPPORT_PLAN_UPDATED, module=AuditModule.CHILD_DEVELOPMENT, record_id=item.id, old_values=old, new_values=payload.model_dump(exclude_unset=True))
    db.commit(); db.refresh(item)
    return plan_row(db, item, user)


def plan_status_action(plan_id: int, status: str, permission: str, db: Session, user: User):
    item = support_plan_or_404(db, plan_id)
    set_plan_status(item, status, user)
    add_audit_log(db, user_id=user.id, action=AuditAction.BEHAVIOR_SUPPORT_PLAN_STATUS_CHANGED, module=AuditModule.CHILD_DEVELOPMENT, record_id=item.id, new_values={"plan_status": status, "permission": permission})
    db.commit(); db.refresh(item)
    return plan_row(db, item, user)


@router.post("/behavior-support-plans/{plan_id}/activate", response_model=BehaviorSupportPlanResponse)
def activate_behavior_support_plan(plan_id: int, db: Session = Depends(get_db), user: User = Depends(require_permission("development.support_plan.activate"))):
    return plan_status_action(plan_id, "Active", "activate", db, user)


@router.post("/behavior-support-plans/{plan_id}/review", response_model=BehaviorSupportPlanResponse)
def review_behavior_support_plan(plan_id: int, db: Session = Depends(get_db), user: User = Depends(require_permission("development.support_plan.review"))):
    return plan_status_action(plan_id, "Under Review", "review", db, user)


@router.post("/behavior-support-plans/{plan_id}/complete", response_model=BehaviorSupportPlanResponse)
def complete_behavior_support_plan(plan_id: int, db: Session = Depends(get_db), user: User = Depends(require_permission("development.support_plan.complete"))):
    return plan_status_action(plan_id, "Completed", "complete", db, user)


@router.post("/behavior-support-plans/{plan_id}/close", response_model=BehaviorSupportPlanResponse)
def close_behavior_support_plan(plan_id: int, db: Session = Depends(get_db), user: User = Depends(require_permission("development.support_plan.close"))):
    return plan_status_action(plan_id, "Closed", "close", db, user)


@router.post("/behavior-support-plans/{plan_id}/cancel", response_model=BehaviorSupportPlanResponse)
def cancel_behavior_support_plan(plan_id: int, db: Session = Depends(get_db), user: User = Depends(require_permission("development.support_plan.cancel"))):
    return plan_status_action(plan_id, "Cancelled", "cancel", db, user)


@router.delete("/behavior-support-plans/{plan_id}", response_model=BehaviorSupportPlanResponse)
def archive_behavior_support_plan(plan_id: int, db: Session = Depends(get_db), user: User = Depends(require_permission("development.support_plan.delete"))):
    return plan_status_action(plan_id, "Archived", "delete", db, user)


@router.get("/behavior-support-plans/{plan_id}/notes", response_model=list[BehaviorSupportPlanNoteResponse])
def behavior_support_plan_notes(plan_id: int, db: Session = Depends(get_db), _user: User = Depends(require_permission("development.support_plan.notes.view"))):
    item = support_plan_or_404(db, plan_id)
    return db.scalars(select(ChildBehaviorSupportPlanNote).where(ChildBehaviorSupportPlanNote.plan_id == item.id).order_by(ChildBehaviorSupportPlanNote.note_date.desc(), ChildBehaviorSupportPlanNote.id.desc())).all()


@router.post("/behavior-support-plans/{plan_id}/notes", response_model=BehaviorSupportPlanNoteResponse, status_code=201)
def create_behavior_support_plan_note(plan_id: int, payload: BehaviorSupportPlanNoteCreate, db: Session = Depends(get_db), user: User = Depends(require_permission("development.support_plan.notes.create"))):
    plan = support_plan_or_404(db, plan_id)
    item = ChildBehaviorSupportPlanNote(**payload.model_dump(), plan_id=plan.id, child_id=plan.child_id, created_by_user_id=user.id)
    item.progress_note = support_safe_text(item.progress_note)
    item.staff_action_taken = support_safe_text(item.staff_action_taken)
    item.child_response = support_safe_text(item.child_response)
    item.next_step = support_safe_text(item.next_step)
    db.add(item)
    add_audit_log(db, user_id=user.id, action=AuditAction.BEHAVIOR_SUPPORT_PLAN_NOTE_CREATED, module=AuditModule.CHILD_DEVELOPMENT, record_id=plan.id, new_values={"note_type": item.note_type})
    db.commit(); db.refresh(item)
    return item


@router.put("/behavior-support-plan-notes/{note_id}", response_model=BehaviorSupportPlanNoteResponse)
def update_behavior_support_plan_note(note_id: int, payload: BehaviorSupportPlanNoteUpdate, db: Session = Depends(get_db), user: User = Depends(require_permission("development.support_plan.notes.update"))):
    item = support_note_or_404(db, note_id)
    for key, value in payload.model_dump(exclude_unset=True).items():
        if isinstance(value, str):
            value = support_safe_text(value)
        setattr(item, key, value)
    add_audit_log(db, user_id=user.id, action=AuditAction.BEHAVIOR_SUPPORT_PLAN_NOTE_UPDATED, module=AuditModule.CHILD_DEVELOPMENT, record_id=item.plan_id, new_values=payload.model_dump(exclude_unset=True))
    db.commit(); db.refresh(item)
    return item


@router.delete("/behavior-support-plan-notes/{note_id}")
def delete_behavior_support_plan_note(note_id: int, db: Session = Depends(get_db), user: User = Depends(require_permission("development.support_plan.notes.delete"))):
    item = support_note_or_404(db, note_id)
    plan_id = item.plan_id
    db.delete(item)
    add_audit_log(db, user_id=user.id, action=AuditAction.BEHAVIOR_SUPPORT_PLAN_NOTE_DELETED, module=AuditModule.CHILD_DEVELOPMENT, record_id=plan_id)
    db.commit()
    return {"deleted": True}


@router.get("/reports/child-development")
def child_development_report(
    month: int | None = Query(default=None, ge=1, le=12),
    year: int | None = Query(default=None, ge=2000, le=2100),
    child_id: int | None = None,
    review_status: str | None = None,
    observation_frequency: str | None = None,
    district: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("development.view")),
):
    today = date.today()
    report_month = month if isinstance(month, int) else today.month
    report_year = year if isinstance(year, int) else today.year
    observations = []
    for child in db.scalars(child_base_query(child_id=child_id, district=district)).all():
        summary = development_summary(db, child.id, user)
        query = observation_query().where(
            ChildDevelopmentObservation.child_id == child.id,
            ChildDevelopmentObservation.review_status != "Archived",
            extract("year", ChildDevelopmentObservation.observation_date) == report_year,
            extract("month", ChildDevelopmentObservation.observation_date) == report_month,
        )
        if review_status:
            query = query.where(ChildDevelopmentObservation.review_status == review_status)
        if observation_frequency:
            query = query.where(ChildDevelopmentObservation.observation_frequency == observation_frequency)
        child_observation_rows = [obs_response(item, user) for item in db.scalars(query.order_by(ChildDevelopmentObservation.observation_date.desc())).all()]
        observations.extend(child_observation_rows)

    missing_rows = missing_monthly_rows(db, report_month, report_year, district=district)
    if child_id:
        missing_rows = [row for row in missing_rows if row["child_id"] == child_id]
    talent = talent_rows(db, user, month=report_month, year=report_year, child_id=child_id, district=district)
    return {
        "summary": {
            "reviewed_this_month": len({item.child_id for item in observations if item.observation_frequency == "Monthly"}),
            "missing_monthly": len(missing_rows),
            "needs_follow_up": sum(1 for item in observations if item.review_status == "Needs Follow-up"),
            "urgent_flags": sum(1 for item in observations if item.urgent_flag),
            "support_needs": sum(1 for row in talent if row["support_needs"]),
            "talent_indicators": sum(1 for row in talent if row["possible_areas_of_interest"]),
        },
        "observations": observations,
        "missing_monthly_observations": missing_rows,
        "talent_summary": talent,
    }


@router.get("/reports/development-ai-summaries", response_model=list[DevelopmentAISummaryResponse])
def development_ai_summary_report(
    month: int | None = Query(default=None, ge=1, le=12),
    year: int | None = Query(default=None, ge=2000, le=2100),
    child: str | None = None,
    trend_status: str | None = None,
    attention_level: str | None = None,
    approval_status: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("development.ai_summary.view")),
):
    month = month if isinstance(month, int) else None
    year = year if isinstance(year, int) else None
    query = select(ChildDevelopmentAISummary, Child).join(Child, Child.id == ChildDevelopmentAISummary.child_id).where(ChildDevelopmentAISummary.approval_status != "Archived")
    if month:
        query = query.where(ChildDevelopmentAISummary.summary_period_month == month)
    if year:
        query = query.where(ChildDevelopmentAISummary.summary_period_year == year)
    if trend_status:
        query = query.where(ChildDevelopmentAISummary.trend_status == trend_status)
    if attention_level:
        query = query.where(ChildDevelopmentAISummary.attention_level == attention_level)
    if approval_status:
        query = query.where(ChildDevelopmentAISummary.approval_status == approval_status)
    if child:
        query = query.where((Child.full_name.ilike(f"%{child}%")) | (Child.child_id.ilike(f"%{child}%")))
    if not any(role.name in {"Admin", "Manager", "Counselor"} for role in user.roles):
        query = query.where(ChildDevelopmentAISummary.approval_status == "Approved")
    rows = db.execute(query.order_by(ChildDevelopmentAISummary.generated_at.desc(), ChildDevelopmentAISummary.id.desc())).all()
    return [summary_row(clean_ai_summary(item, user), child_row) for item, child_row in rows]


@router.get("/reports/behavior-support-plans")
def behavior_support_plan_report(
    child_id: int | None = None,
    plan_status: str | None = None,
    plan_type: str | None = None,
    priority_level: str | None = None,
    month: int | None = Query(default=None, ge=1, le=12),
    year: int | None = Query(default=None, ge=2000, le=2100),
    district: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("development.support_plan.view")),
):
    today = date.today()
    month = month if isinstance(month, int) else None
    year = year if isinstance(year, int) else None
    query = select(ChildBehaviorSupportPlan, Child).join(Child, Child.id == ChildBehaviorSupportPlan.child_id).where(ChildBehaviorSupportPlan.plan_status != "Archived")
    if child_id:
        query = query.where(ChildBehaviorSupportPlan.child_id == child_id)
    if plan_status:
        query = query.where(ChildBehaviorSupportPlan.plan_status == plan_status)
    if plan_type:
        query = query.where(ChildBehaviorSupportPlan.plan_type == plan_type)
    if priority_level:
        query = query.where(ChildBehaviorSupportPlan.priority_level == priority_level)
    if month:
        query = query.where(extract("month", ChildBehaviorSupportPlan.created_at) == month)
    if year:
        query = query.where(extract("year", ChildBehaviorSupportPlan.created_at) == year)
    if district:
        query = query.where(Child.district.ilike(f"%{district}%"))
    if not any(role.name in {"Admin", "Manager", "Counselor", "Warden"} for role in user.roles):
        query = query.where(ChildBehaviorSupportPlan.plan_status == "Active")
    rows = [plan for plan, _child in db.execute(query.order_by(ChildBehaviorSupportPlan.created_at.desc(), ChildBehaviorSupportPlan.id.desc())).all()]
    completed_this_month = sum(1 for row in rows if row.plan_status == "Completed" and row.closed_at and row.closed_at.month == today.month and row.closed_at.year == today.year)
    return {
        "summary": {
            "active_plans": sum(1 for row in rows if row.plan_status == "Active"),
            "under_review": sum(1 for row in rows if row.plan_status == "Under Review"),
            "high_priority": sum(1 for row in rows if row.priority_level == "High"),
            "urgent_review": sum(1 for row in rows if row.priority_level == "Urgent Review"),
            "completed_this_month": completed_this_month,
            "overdue_reviews": sum(1 for row in rows if row.review_date and row.review_date < today and row.plan_status in {"Active", "Under Review"}),
        },
        "plans": [plan_row(db, row, user) for row in rows],
    }


@router.get("/reports/monthly-development-missing")
def monthly_missing(
    month: int = Query(default_factory=lambda: date.today().month, ge=1, le=12),
    year: int = Query(default_factory=lambda: date.today().year, ge=2000, le=2100),
    district: str | None = None,
    status: str | None = None,
    db: Session = Depends(get_db),
    _user: User = Depends(require_permission("development.view")),
):
    return missing_monthly_rows(db, month, year, district=district, status=status)


@router.get("/reports/child-talent-summary")
def talent_summary(
    month: int | None = Query(default=None, ge=1, le=12),
    year: int | None = Query(default=None, ge=2000, le=2100),
    child_id: int | None = None,
    district: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("development.view")),
):
    return talent_rows(db, user, month=month, year=year, child_id=child_id, district=district)


@router.get("/dashboard/development")
def development_dashboard(db: Session = Depends(get_db), _user: User = Depends(require_permission("development.view"))):
    today = date.today()
    reviewed = db.scalar(select(func.count()).select_from(ChildDevelopmentObservation).where(ChildDevelopmentObservation.observation_frequency == "Monthly", extract("year", ChildDevelopmentObservation.observation_date) == today.year, extract("month", ChildDevelopmentObservation.observation_date) == today.month, ChildDevelopmentObservation.review_status != "Archived")) or 0
    pending = len(missing_monthly_rows(db, today.month, today.year))
    follow_up = db.scalar(select(func.count()).select_from(ChildDevelopmentObservation).where(ChildDevelopmentObservation.review_status == "Needs Follow-up")) or 0
    urgent = db.scalar(select(func.count()).select_from(ChildDevelopmentObservation).where(ChildDevelopmentObservation.urgent_flag.is_(True), ChildDevelopmentObservation.review_status.in_(["Draft", "Submitted", "Reviewed", "Needs Follow-up"]))) or 0
    return {"children_reviewed_this_month": reviewed, "children_pending_monthly_review": pending, "observations_needing_follow_up": follow_up, "urgent_development_flags": urgent}


def pdf_response(db: Session, user: User, title: str, rows: list[dict], filename: str):
    stream = build_pdf_report(title, rows, user.username, {}, report_branding(db))
    add_audit_log(db, user_id=user.id, action=AuditAction.EXPORT_PDF, module=AuditModule.IMPORT_EXPORT, new_values={"report_type": filename})
    db.commit()
    return StreamingResponse(stream, media_type="application/pdf", headers={"Content-Disposition": f'attachment; filename="{filename}.pdf"'})


def ai_summary_pdf_rows(item: ChildDevelopmentAISummary, user: User) -> list[dict]:
    clean = clean_ai_summary(item, user)
    rows = [
        {"section": "Overall Summary", "value": clean.overall_summary or "Not recorded"},
        {"section": "Positive Strengths", "value": clean.positive_strengths_summary or "Not recorded"},
        {"section": "Support Needs", "value": clean.support_needs_summary or "Not recorded"},
        {"section": "Talent / Interests", "value": clean.talent_interest_summary or "Not recorded"},
        {"section": "Behavior Trend", "value": clean.behavior_trend_summary or "Not recorded"},
        {"section": "Learning Behavior", "value": clean.learning_behavior_summary or "Not recorded"},
        {"section": "Social Behavior", "value": clean.social_behavior_summary or "Not recorded"},
        {"section": "Risk Attention", "value": clean.risk_attention_summary or "Not recorded"},
        {"section": "Staff Actions", "value": clean.recommended_staff_actions or "Not recorded"},
        {"section": "Counselor Actions", "value": clean.recommended_counselor_actions or "Restricted"},
        {"section": "Next Review Date", "value": clean.next_review_date or "Not scheduled"},
        {"section": "Trend Status", "value": clean.trend_status},
        {"section": "Attention Level", "value": clean.attention_level if not clean.is_sensitive else "Restricted"},
        {"section": "Footer Note", "value": SAFE_FOOTER},
    ]
    if clean.internal_notes:
        rows.append({"section": "Internal Notes", "value": clean.internal_notes})
    return rows


def behavior_plan_pdf_rows(db: Session, item: ChildBehaviorSupportPlan, user: User) -> list[dict]:
    row = plan_row(db, item, user)
    rows = [
        {"section": "Plan Code", "value": row["plan_code"]},
        {"section": "Plan Title", "value": row["plan_title"]},
        {"section": "Plan Type", "value": row["plan_type"]},
        {"section": "Priority", "value": row["priority_level"]},
        {"section": "Status", "value": row["plan_status"]},
        {"section": "Identified Behavior", "value": row.get("identified_behavior") or "Not recorded"},
        {"section": "Possible Triggers", "value": row.get("possible_triggers") or "Not recorded"},
        {"section": "Replacement Positive Behavior", "value": row.get("replacement_positive_behavior") or "Not recorded"},
        {"section": "Prevention Strategies", "value": row.get("prevention_strategies") or "Not recorded"},
        {"section": "Staff Response Plan", "value": row.get("staff_response_plan") or "Not recorded"},
        {"section": "De-escalation Steps", "value": row.get("de_escalation_steps") or "Not recorded"},
        {"section": "Positive Reinforcement", "value": row.get("positive_reinforcement_plan") or "Not recorded"},
        {"section": "Counselor Recommendations", "value": row.get("counselor_recommendations") or "Restricted"},
        {"section": "Review Date", "value": row.get("review_date") or "Not scheduled"},
        {"section": "Footer Note", "value": PLAN_FOOTER},
    ]
    return rows


@router.get("/exports/child-development-profile/{child_id}.pdf")
def export_child_development_profile(child_id: int, db: Session = Depends(get_db), user: User = Depends(require_permission("development.export"))):
    profile = child_development_profile(child_id, db, user)
    summary = profile["summary"]
    rows = [{"section": "Latest Observation", "value": summary["latest_observation_date"] or "Not recorded"}, {"section": "Review Status", "value": summary["review_status"]}, {"section": "Monthly Review", "value": summary["monthly_review_status"]}, {"section": "Positive Strengths", "value": ", ".join(summary["positive_strengths"]) or "Not recorded"}, {"section": "Support Needs", "value": ", ".join(summary["support_needs"]) or "Not recorded"}, {"section": "Possible Areas of Interest", "value": ", ".join(summary["possible_areas_of_interest"]) or "Not recorded"}, {"section": "Suggested Support", "value": summary["recommended_support"]}, {"section": "Safe Summary", "value": summary["summary_text"]}]
    return pdf_response(db, user, "Child Development Profile", rows, f"ccms-child-development-profile-{child_id}")


@router.get("/exports/development-ai-summary/{summary_id}.pdf")
def export_development_ai_summary(summary_id: int, db: Session = Depends(get_db), user: User = Depends(require_permission("development.ai_summary.export"))):
    item = ai_summary_or_404(db, summary_id)
    return pdf_response(db, user, "AI-Assisted Child Development Summary", ai_summary_pdf_rows(item, user), f"ccms-development-ai-summary-{summary_id}")


@router.get("/exports/behavior-support-plan/{plan_id}.pdf")
def export_behavior_support_plan(plan_id: int, db: Session = Depends(get_db), user: User = Depends(require_permission("development.support_plan.export"))):
    item = support_plan_or_404(db, plan_id)
    return pdf_response(db, user, "Behavior Support Plan", behavior_plan_pdf_rows(db, item, user), f"ccms-behavior-support-plan-{plan_id}")


@router.get("/exports/child-behavior-support-plans/{child_id}.pdf")
def export_child_behavior_support_plans(child_id: int, db: Session = Depends(get_db), user: User = Depends(require_permission("development.support_plan.export"))):
    rows = db.scalars(select(ChildBehaviorSupportPlan).where(ChildBehaviorSupportPlan.child_id == child_id, ChildBehaviorSupportPlan.plan_status.in_(["Active", "Under Review", "Completed", "Closed"])).order_by(ChildBehaviorSupportPlan.created_at.desc())).all()
    pdf_rows = []
    for item in rows:
        pdf_rows.extend(behavior_plan_pdf_rows(db, item, user))
    if not pdf_rows:
        pdf_rows = [{"section": "Support Plans", "value": "No active behavior support plan found."}, {"section": "Footer Note", "value": PLAN_FOOTER}]
    return pdf_response(db, user, "Behavior Support Plan", pdf_rows, f"ccms-child-behavior-support-plans-{child_id}")


@router.get("/exports/child-development-ai-summary/{child_id}.pdf")
def export_child_development_ai_summary(child_id: int, db: Session = Depends(get_db), user: User = Depends(require_permission("development.ai_summary.export"))):
    item = db.scalar(select(ChildDevelopmentAISummary).where(ChildDevelopmentAISummary.child_id == child_id, ChildDevelopmentAISummary.approval_status == "Approved").order_by(ChildDevelopmentAISummary.approved_at.desc(), ChildDevelopmentAISummary.id.desc()).limit(1))
    if item is None:
        raise HTTPException(404, "Approved development AI summary not found")
    return pdf_response(db, user, "AI-Assisted Child Development Summary", ai_summary_pdf_rows(item, user), f"ccms-child-development-ai-summary-{child_id}")


@router.get("/exports/child-development-observations.pdf")
def export_development_observations(db: Session = Depends(get_db), user: User = Depends(require_permission("development.export"))):
    report = child_development_report(db=db, user=user)
    rows = [
        {
            "child_id": item.child_id,
            "observation_date": item.observation_date,
            "frequency": item.observation_frequency,
            "review_status": item.review_status,
            "urgent_flag": item.urgent_flag,
        }
        for item in report["observations"]
    ]
    return pdf_response(db, user, "Child Development Observations", rows, "ccms-child-development-observations")


@router.get("/exports/monthly-development-summary.pdf")
def export_monthly_development_summary(month: int = Query(default_factory=lambda: date.today().month, ge=1, le=12), year: int = Query(default_factory=lambda: date.today().year, ge=2000, le=2100), db: Session = Depends(get_db), user: User = Depends(require_permission("development.export"))):
    rows = missing_monthly_rows(db, month, year)
    return pdf_response(db, user, f"Monthly Development Summary {year}-{month:02d}", rows, f"ccms-monthly-development-summary-{year}-{month:02d}")


@router.get("/exports/child-talent-summary.pdf")
def export_child_talent_summary(db: Session = Depends(get_db), user: User = Depends(require_permission("development.export"))):
    return pdf_response(db, user, "Child Talent Summary", talent_rows(db, user), "ccms-child-talent-summary")


@router.get("/exports/development-ai-summaries.pdf")
def export_development_ai_summaries(db: Session = Depends(get_db), user: User = Depends(require_permission("development.ai_summary.export"))):
    rows = development_ai_summary_report(db=db, user=user)
    safe_rows = [{"child": row.get("child_code"), "period": f"{row['summary_period_year']}-{row['summary_period_month']:02d}", "trend": row["trend_status"], "attention_level": "Restricted" if row.get("is_sensitive") else row["attention_level"], "approval_status": row["approval_status"], "source_observations": row["source_observation_count"], "last_generated": row["generated_at"]} for row in rows]
    safe_rows.append({"child": "Footer", "period": SAFE_FOOTER, "trend": "", "attention_level": "", "approval_status": "", "source_observations": "", "last_generated": ""})
    return pdf_response(db, user, "AI-Assisted Child Development Summary", safe_rows, "ccms-development-ai-summaries")


@router.get("/exports/behavior-support-plans.pdf")
def export_behavior_support_plans(db: Session = Depends(get_db), user: User = Depends(require_permission("development.support_plan.export"))):
    report = behavior_support_plan_report(db=db, user=user)
    rows = [{"plan_code": row["plan_code"], "child": row["child_code"], "plan_type": row["plan_type"], "priority": row["priority_level"], "status": row["plan_status"], "review_date": row["review_date"] or "Not scheduled"} for row in report["plans"]]
    rows.append({"plan_code": "Footer", "child": PLAN_FOOTER, "plan_type": "", "priority": "", "status": "", "review_date": ""})
    return pdf_response(db, user, "Behavior Support Plan", rows, "ccms-behavior-support-plans")
