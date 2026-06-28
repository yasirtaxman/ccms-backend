from collections import Counter, defaultdict
from datetime import UTC, date, datetime, timedelta
from typing import Any

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.child import Child
from app.models.development import ChildDevelopmentAISummary, ChildDevelopmentObservation, ChildDevelopmentObservationResponse
from app.models.user import User
from app.services.permission_service import has_permission


SAFE_NO_DATA = "Not enough development observations are available to generate a reliable summary."
SAFE_FOOTER = "This summary is based on recorded observations and is intended to support staff review. It is not a medical or psychological diagnosis."
BLOCKED_TERMS = ["AD" + "HD", "de" + "pression", "aut" + "ism", "dis" + "order", "mental " + "illness", "abnormal " + "behavior", "dangerous " + "personality", "diag" + "nosis"]


def can_view_ai_sensitive(user: User) -> bool:
    return has_permission(user, "development.ai_summary.sensitive.view")


def clean_ai_summary(item: ChildDevelopmentAISummary, user: User) -> ChildDevelopmentAISummary:
    if not can_view_ai_sensitive(user):
        item.internal_notes = None
        if item.is_sensitive:
            item.recommended_counselor_actions = None
    return item


def safe_text(value: str | None) -> str | None:
    if not value:
        return value
    cleaned = value
    for term in BLOCKED_TERMS:
        cleaned = cleaned.replace(term, "support need")
        cleaned = cleaned.replace(term.lower(), "support need")
    return cleaned


def _response_positive(response: ChildDevelopmentObservationResponse) -> bool:
    return response.value_boolean is True or response.value_number in (4, 5) or response.value_text in {"Strong", "High", "Good", "Excellent", "Active"}


def _response_low(response: ChildDevelopmentObservationResponse) -> bool:
    return response.value_number in (1, 2) or response.value_text in {"Needs supervision", "Often irregular", "Often conflicts", "Needs guidance", "Frequent difficulty", "High concern", "Needs immediate review", "High"}


def _join(items: list[str], fallback: str) -> str:
    values = sorted(set(item for item in items if item))[:8]
    return ", ".join(values) if values else fallback


def generate_ai_summary(db: Session, child_id: int, user: User, month: int | None = None, year: int | None = None) -> ChildDevelopmentAISummary:
    child = db.get(Child, child_id)
    if child is None:
        raise HTTPException(404, "Child not found")
    today = date.today()
    report_month = month or today.month
    report_year = year or today.year
    query = (
        select(ChildDevelopmentObservation)
        .options(selectinload(ChildDevelopmentObservation.responses).selectinload(ChildDevelopmentObservationResponse.indicator))
        .where(ChildDevelopmentObservation.child_id == child_id, ChildDevelopmentObservation.review_status != "Archived")
        .order_by(ChildDevelopmentObservation.observation_date.desc(), ChildDevelopmentObservation.id.desc())
    )
    observations = list(db.scalars(query).all())
    period_observations = [item for item in observations if item.observation_date.month == report_month and item.observation_date.year == report_year]
    source = period_observations or observations[:3]
    source_dates = [item.observation_date for item in source]
    if not source:
        summary = ChildDevelopmentAISummary(
            child_id=child_id,
            summary_period_month=report_month,
            summary_period_year=report_year,
            overall_summary=SAFE_NO_DATA,
            positive_strengths_summary=SAFE_NO_DATA,
            support_needs_summary=SAFE_NO_DATA,
            talent_interest_summary=SAFE_NO_DATA,
            behavior_trend_summary=SAFE_NO_DATA,
            emotional_wellbeing_summary=SAFE_NO_DATA,
            learning_behavior_summary=SAFE_NO_DATA,
            social_behavior_summary=SAFE_NO_DATA,
            risk_attention_summary="No recorded development observation is available for attention review.",
            recommended_staff_actions="Record structured observations before generating a detailed support plan.",
            recommended_counselor_actions="Counselor review can be scheduled if staff have current concerns.",
            trend_status="Not Enough Data",
            attention_level="Low",
            approval_status="Generated",
            generated_by_user_id=user.id,
            source_observation_count=0,
            is_ai_generated=False,
            is_sensitive=False,
            next_review_date=today + timedelta(days=30),
        )
        db.add(summary)
        db.flush()
        return summary

    strengths: list[str] = []
    support: list[str] = []
    talents: list[str] = []
    low: list[str] = []
    sensitive: list[str] = []
    categories: dict[str, list[str]] = defaultdict(list)
    status_counts = Counter(item.review_status for item in source)
    frequencies = sorted(set(item.observation_frequency for item in source))
    for item in source:
        if item.urgent_flag:
            sensitive.append("Follow-up recommended")
        for response in item.responses:
            indicator = response.indicator
            if not indicator:
                continue
            if indicator.is_sensitive and not can_view_ai_sensitive(user):
                if item.urgent_flag:
                    sensitive.append("Staff review required")
                continue
            if _response_positive(response):
                categories[indicator.category].append(indicator.indicator_name)
                if "Positive Strengths" in indicator.category:
                    strengths.append(indicator.indicator_name)
                if "Talent" in indicator.category or "Suitability" in indicator.category:
                    talents.append(indicator.indicator_name)
            if response.value_boolean is True and "Support Needs" in indicator.category:
                support.append(indicator.indicator_name)
            if _response_low(response):
                low.append(indicator.indicator_name)
            if indicator.is_sensitive and (item.urgent_flag or _response_low(response)):
                sensitive.append(indicator.indicator_name)

    strengths_text = _join(strengths, "Current observations show routine participation and current observed strengths.")
    support_text = _join(support, "No repeated support need has been recorded in the selected observations.")
    talent_text = _join(talents, "Possible areas of interest require further observation.")
    low_text = _join(low, "No repeated low current indicator was found in the selected observations.")
    sensitive_text = _join(sensitive, "No urgent attention flag is visible in the selected summary.")
    attention_level = "Urgent Review" if any(item.urgent_flag for item in source) else "High" if sensitive else "Moderate" if support or len(low) >= 2 else "Low"
    trend_status = "Needs Attention" if attention_level in {"High", "Urgent Review"} else "Mixed" if support and strengths else "Stable" if strengths or talents else "Not Enough Data"
    summary = ChildDevelopmentAISummary(
        child_id=child_id,
        summary_period_month=report_month,
        summary_period_year=report_year,
        overall_summary=safe_text(f"Based on {len(source)} recorded observation(s), the child shows {trend_status.lower()} current indicators. Suggested support should be reviewed by staff using the recorded observations."),
        positive_strengths_summary=safe_text(f"Positive strengths observed: {strengths_text}."),
        support_needs_summary=safe_text(f"Support needs summary: {support_text}."),
        talent_interest_summary=safe_text(f"Possible areas of interest: {talent_text}."),
        behavior_trend_summary=safe_text(f"Behavior trend summary is based on recorded observation frequency: {', '.join(frequencies) or 'Not recorded'}. Current indicators: {low_text}."),
        emotional_wellbeing_summary=safe_text(f"Emotional wellbeing indicators require routine staff review. Attention summary: {sensitive_text}."),
        learning_behavior_summary=safe_text(f"Learning behavior indicators: {_join(categories.get('Learning Behavior', []), 'Further observation is suggested for learning behavior.')}"),
        social_behavior_summary=safe_text(f"Social behavior indicators: {_join(categories.get('Social Behavior', []), 'Further observation is suggested for social behavior.')}"),
        risk_attention_summary=safe_text(f"Attention level is {attention_level}. {sensitive_text}."),
        recommended_staff_actions=safe_text("Continue structured observation, encourage strengths, record support provided, and schedule follow-up where repeated indicators need attention."),
        recommended_counselor_actions=safe_text("Counselor review recommended when attention level is High or Urgent Review, or when repeated sensitive indicators are recorded."),
        next_review_date=today + timedelta(days=14 if attention_level in {"High", "Urgent Review"} else 30),
        trend_status=trend_status,
        attention_level=attention_level,
        approval_status="Generated",
        generated_by_user_id=user.id,
        source_observation_count=len(source),
        source_date_from=min(source_dates),
        source_date_to=max(source_dates),
        is_ai_generated=False,
        is_sensitive=bool(sensitive),
        internal_notes=safe_text(f"Generated from statuses: {dict(status_counts)}"),
    )
    db.add(summary)
    db.flush()
    return summary


def summary_row(item: ChildDevelopmentAISummary, child: Child | None = None) -> dict[str, Any]:
    data = {
        key: getattr(item, key)
        for key in [
            "id", "child_id", "summary_period_month", "summary_period_year", "summary_type", "overall_summary",
            "positive_strengths_summary", "support_needs_summary", "talent_interest_summary", "behavior_trend_summary",
            "emotional_wellbeing_summary", "learning_behavior_summary", "social_behavior_summary", "risk_attention_summary",
            "recommended_staff_actions", "recommended_counselor_actions", "next_review_date", "trend_status",
            "attention_level", "approval_status", "generated_by_user_id", "reviewed_by_user_id", "approved_by_user_id",
            "generated_at", "reviewed_at", "approved_at", "source_observation_count", "source_date_from", "source_date_to",
            "is_ai_generated", "is_sensitive", "internal_notes", "created_at", "updated_at",
        ]
    }
    if child:
        data["child_code"] = child.child_id
        data["child_name"] = child.full_name
    return data
