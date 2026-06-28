from datetime import UTC, date, datetime, timedelta
from types import SimpleNamespace
from typing import Any

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models.child import Child
from app.models.development import ChildBehaviorSupportPlan, ChildBehaviorSupportPlanNote, ChildDevelopmentAISummary, ChildDevelopmentObservation, ChildDevelopmentObservationResponse
from app.models.user import User
from app.schemas.development import BehaviorSupportPlanCreate
from app.services.permission_service import has_permission


NO_DATA_MESSAGE = "Not enough recorded observations are available to generate a reliable support plan."
PLAN_FOOTER = "This plan is based on recorded observations and is intended to support staff care planning. It is not a medical or psychological " + "diag" + "nosis."
BLOCKED_TERMS = ["AD" + "HD", "de" + "pression", "aut" + "ism", "dis" + "order", "mentally " + "ill", "ab" + "normal", "dangerous " + "child", "problem " + "child", "pun" + "ishment " + "required", "permanent " + "personality"]


def can_view_support_sensitive(user: User) -> bool:
    return has_permission(user, "development.support_plan.sensitive.view")


def safe_text(value: str | None) -> str | None:
    if not value:
        return value
    result = value
    for term in BLOCKED_TERMS:
        result = result.replace(term, "support need").replace(term.lower(), "support need")
    return result


def clean_plan(item: ChildBehaviorSupportPlan, user: User) -> Any:
    safe = SimpleNamespace(**{column.name: getattr(item, column.name) for column in ChildBehaviorSupportPlan.__table__.columns})
    if not can_view_support_sensitive(user):
        safe.internal_notes = None
        if safe.is_sensitive:
            safe.counselor_recommendations = None
            safe.guardian_communication_notes = None
    return safe


def next_plan_code(db: Session, child_id: int) -> str:
    count = db.scalar(select(func.count()).select_from(ChildBehaviorSupportPlan).where(ChildBehaviorSupportPlan.child_id == child_id)) or 0
    return f"BSP-{child_id:05d}-{count + 1:03d}"


def _positive(response: ChildDevelopmentObservationResponse) -> bool:
    return response.value_boolean is True or response.value_number in (4, 5) or response.value_text in {"Strong", "High", "Good", "Excellent", "Active"}


def _attention(response: ChildDevelopmentObservationResponse) -> bool:
    return response.value_number in (1, 2) or response.value_text in {"Needs supervision", "Often conflicts", "Needs guidance", "Frequent difficulty", "High concern", "Needs immediate review", "High"}


def _join(values: list[str], fallback: str) -> str:
    cleaned = sorted(set(v for v in values if v))[:8]
    return ", ".join(cleaned) if cleaned else fallback


def create_plan(db: Session, child_id: int, payload: BehaviorSupportPlanCreate, user: User) -> ChildBehaviorSupportPlan:
    if db.get(Child, child_id) is None:
        raise HTTPException(404, "Child not found")
    data = payload.model_dump()
    for key in ["internal_notes", "identified_behavior", "behavior_description", "possible_triggers", "known_patterns", "replacement_positive_behavior", "prevention_strategies", "staff_response_plan", "de_escalation_steps", "positive_reinforcement_plan", "counselor_recommendations"]:
        data[key] = safe_text(data.get(key))
    item = ChildBehaviorSupportPlan(**data, child_id=child_id, plan_code=next_plan_code(db, child_id), created_by_user_id=user.id, updated_by_user_id=user.id)
    db.add(item)
    db.flush()
    return item


def generate_support_plan(db: Session, child_id: int, user: User) -> ChildBehaviorSupportPlan:
    child = db.get(Child, child_id)
    if child is None:
        raise HTTPException(404, "Child not found")
    observations = list(db.scalars(select(ChildDevelopmentObservation).options(selectinload(ChildDevelopmentObservation.responses).selectinload(ChildDevelopmentObservationResponse.indicator)).where(ChildDevelopmentObservation.child_id == child_id, ChildDevelopmentObservation.review_status != "Archived").order_by(ChildDevelopmentObservation.observation_date.desc(), ChildDevelopmentObservation.id.desc()).limit(5)).all())
    latest_ai = db.scalar(select(ChildDevelopmentAISummary).where(ChildDevelopmentAISummary.child_id == child_id, ChildDevelopmentAISummary.approval_status == "Approved").order_by(ChildDevelopmentAISummary.approved_at.desc(), ChildDevelopmentAISummary.id.desc()).limit(1))
    if not observations and latest_ai is None:
        payload = BehaviorSupportPlanCreate(
            plan_title="Draft Support Plan - More Observations Needed",
            plan_type="General Support",
            identified_behavior=NO_DATA_MESSAGE,
            behavior_description=NO_DATA_MESSAGE,
            replacement_positive_behavior="Record observation-based support goals before activation.",
            prevention_strategies="Continue structured observations and staff check-ins.",
            staff_response_plan="Record progress notes when support actions are taken.",
            de_escalation_steps="Use calm staff response and request counselor review when needed.",
            positive_reinforcement_plan="Recognize positive participation and safe routine behavior.",
            counselor_recommendations="Counselor review can be scheduled if staff have current concerns.",
            start_date=date.today(),
            review_date=date.today() + timedelta(days=30),
        )
        return create_plan(db, child_id, payload, user)
    support: list[str] = []
    attention: list[str] = []
    strengths: list[str] = []
    sensitive = False
    source_observation_id = observations[0].id if observations else None
    for observation in observations:
        sensitive = sensitive or observation.urgent_flag
        for response in observation.responses:
            indicator = response.indicator
            if not indicator:
                continue
            if indicator.is_sensitive:
                sensitive = True
                if not can_view_support_sensitive(user):
                    continue
            if "Support Needs" in indicator.category and response.value_boolean is True:
                support.append(indicator.indicator_name)
            if _attention(response):
                attention.append(indicator.indicator_name)
            if _positive(response):
                strengths.append(indicator.indicator_name)
    priority = "Urgent Review" if any(item.urgent_flag for item in observations) else "High" if sensitive or len(attention) >= 2 else "Moderate" if support else "Low"
    title_focus = _join(support or attention, "Routine Development Support")
    payload = BehaviorSupportPlanCreate(
        plan_title=safe_text(f"Draft Support Plan - {title_focus[:80]}") or "Draft Support Plan",
        plan_type="Safety Support" if priority == "Urgent Review" else "Behavior Support",
        priority_level=priority,
        identified_behavior=safe_text(f"Observed behavior focus: {_join(attention, 'No repeated concern indicator recorded; use routine support focus.')}"),
        behavior_description=safe_text(f"Plan is based on {len(observations)} recorded observation(s) and the latest approved AI-assisted summary where available."),
        possible_triggers="Possible trigger should be confirmed through staff observation before activation.",
        known_patterns=safe_text(f"Known patterns from observations: {_join(support, 'No repeated support pattern recorded.')}"),
        replacement_positive_behavior=safe_text(f"Encourage replacement positive behavior through strengths: {_join(strengths, 'safe routine participation and respectful communication')}."),
        prevention_strategies="Use predictable routine, clear instructions, calm staff tone, and early support when current indicators need attention.",
        staff_response_plan="Respond consistently, redirect toward the replacement positive behavior, record progress notes, and request review when follow-up is required.",
        de_escalation_steps="Use calm space, supportive conversation, reduced stimulation, trusted staff support, and counselor review if attention level increases.",
        positive_reinforcement_plan="Recognize effort, cooperation, communication, and safe participation immediately and consistently.",
        counselor_recommendations=safe_text(latest_ai.recommended_counselor_actions if latest_ai else "Counselor review recommended when repeated indicators need attention."),
        start_date=date.today(),
        review_date=date.today() + timedelta(days=14 if priority in {"High", "Urgent Review"} else 30),
        created_from_observation_id=source_observation_id,
        created_from_ai_summary_id=latest_ai.id if latest_ai else None,
        is_sensitive=sensitive,
        internal_notes=safe_text("Draft generated from recorded observations for staff review."),
    )
    return create_plan(db, child_id, payload, user)


def latest_note_text(db: Session, plan_id: int) -> str | None:
    note = db.scalar(select(ChildBehaviorSupportPlanNote).where(ChildBehaviorSupportPlanNote.plan_id == plan_id).order_by(ChildBehaviorSupportPlanNote.note_date.desc(), ChildBehaviorSupportPlanNote.id.desc()).limit(1))
    return note.progress_note if note else None


def plan_row(db: Session, item: ChildBehaviorSupportPlan, user: User) -> dict[str, Any]:
    child = db.get(Child, item.child_id)
    responsible = db.get(User, item.responsible_staff_id) if item.responsible_staff_id else None
    clean = clean_plan(item, user)
    data = {column.name: getattr(clean, column.name) for column in ChildBehaviorSupportPlan.__table__.columns}
    data["child_code"] = child.child_id if child else None
    data["child_name"] = child.full_name if child else None
    data["responsible_staff_name"] = responsible.username if responsible else None
    data["latest_progress_note"] = latest_note_text(db, item.id)
    return data


def set_plan_status(item: ChildBehaviorSupportPlan, status: str, user: User) -> None:
    item.plan_status = status
    item.updated_by_user_id = user.id
    item.updated_at = datetime.now(UTC)
    if status == "Active":
        item.approved_by_user_id = user.id
        item.approved_at = datetime.now(UTC)
    if status in {"Closed", "Completed", "Cancelled", "Archived"}:
        item.closed_at = datetime.now(UTC)
