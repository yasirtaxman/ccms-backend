from datetime import UTC, date, datetime

from sqlalchemy import Boolean, CheckConstraint, Date, DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint, text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


def utc_now() -> datetime:
    return datetime.now(UTC)


class OperationalMixin:
    organization_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    updated_by: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    deleted_by: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=True)


class ChildCaseProfile(OperationalMixin, Base):
    __tablename__ = "child_case_profiles"
    __table_args__ = (
        CheckConstraint("case_status IN ('Open', 'Under Review', 'Closed', 'Transferred')", name="ck_case_profiles_status"),
        CheckConstraint("risk_level IN ('Low', 'Medium', 'High', 'Critical')", name="ck_case_profiles_risk"),
        CheckConstraint("welfare_status IN ('Stable', 'Needs Attention', 'At Risk', 'Critical')", name="ck_case_profiles_welfare"),
        Index("ix_case_profiles_status_risk", "case_status", "risk_level"),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    child_id: Mapped[int] = mapped_column(ForeignKey("children.id", ondelete="RESTRICT"), unique=True, index=True)
    case_number: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    case_opened_date: Mapped[date] = mapped_column(Date)
    case_status: Mapped[str] = mapped_column(String(20), index=True)
    risk_level: Mapped[str] = mapped_column(String(10), index=True)
    welfare_status: Mapped[str] = mapped_column(String(20), index=True)
    assigned_case_worker: Mapped[str | None] = mapped_column(String(255), nullable=True)
    case_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    family_background: Mapped[str | None] = mapped_column(Text, nullable=True)
    psychosocial_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    current_concerns: Mapped[str | None] = mapped_column(Text, nullable=True)
    care_plan_summary: Mapped[str | None] = mapped_column(Text, nullable=True)


class CaseNote(OperationalMixin, Base):
    __tablename__ = "case_notes"
    __table_args__ = (
        CheckConstraint("note_type IN ('General', 'Home Visit', 'Family Contact', 'School Contact', 'Medical Follow-up', 'Counseling', 'Behavior', 'Legal', 'Emergency')", name="ck_case_notes_type"),
        CheckConstraint("visibility IN ('Normal', 'Confidential', 'Restricted')", name="ck_case_notes_visibility"),
        CheckConstraint("follow_up_date IS NULL OR follow_up_date >= note_date", name="ck_case_notes_follow_up_date"),
        Index("ix_case_notes_child_date", "child_id", "note_date"),
        Index("ix_case_notes_follow_up", "follow_up_required", "follow_up_date"),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    child_id: Mapped[int] = mapped_column(ForeignKey("children.id", ondelete="RESTRICT"), index=True)
    case_profile_id: Mapped[int | None] = mapped_column(ForeignKey("child_case_profiles.id", ondelete="RESTRICT"), nullable=True, index=True)
    note_date: Mapped[date] = mapped_column(Date, index=True)
    note_type: Mapped[str] = mapped_column(String(30), index=True)
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text)
    visibility: Mapped[str] = mapped_column(String(15), index=True)
    follow_up_required: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    follow_up_date: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)


class CounselingSession(OperationalMixin, Base):
    __tablename__ = "counseling_sessions"
    __table_args__ = (
        CheckConstraint("session_type IN ('Individual', 'Group', 'Family', 'Emergency')", name="ck_counseling_sessions_type"),
        CheckConstraint("status IN ('Completed', 'Scheduled', 'Cancelled')", name="ck_counseling_sessions_status"),
        CheckConstraint("next_session_date IS NULL OR next_session_date >= session_date", name="ck_counseling_sessions_next_date"),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    child_id: Mapped[int] = mapped_column(ForeignKey("children.id", ondelete="RESTRICT"), index=True)
    session_date: Mapped[date] = mapped_column(Date, index=True)
    counselor_name: Mapped[str] = mapped_column(String(255))
    session_type: Mapped[str] = mapped_column(String(15))
    session_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    observations: Mapped[str | None] = mapped_column(Text, nullable=True)
    recommendations: Mapped[str | None] = mapped_column(Text, nullable=True)
    next_session_date: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(15), index=True)


class IncidentRecord(OperationalMixin, Base):
    __tablename__ = "incident_records"
    __table_args__ = (
        CheckConstraint("incident_type IN ('Behavioral', 'Safety', 'Health', 'Discipline', 'Protection', 'Missing', 'Conflict', 'Other')", name="ck_incidents_type"),
        CheckConstraint("severity IN ('Low', 'Medium', 'High', 'Critical')", name="ck_incidents_severity"),
        CheckConstraint("review_status IN ('Pending Review', 'Reviewed', 'Closed')", name="ck_incidents_review_status"),
        CheckConstraint("reviewed_at IS NULL OR reviewed_at >= incident_date", name="ck_incidents_reviewed_at"),
        Index("ix_incidents_child_date", "child_id", "incident_date"),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    child_id: Mapped[int] = mapped_column(ForeignKey("children.id", ondelete="RESTRICT"), index=True)
    incident_date: Mapped[date] = mapped_column(Date, index=True)
    incident_type: Mapped[str] = mapped_column(String(20), index=True)
    severity: Mapped[str] = mapped_column(String(10), index=True)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    description: Mapped[str] = mapped_column(Text)
    immediate_action_taken: Mapped[str | None] = mapped_column(Text, nullable=True)
    reported_by: Mapped[str] = mapped_column(String(255))
    review_status: Mapped[str] = mapped_column(String(20), index=True)
    reviewed_by: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=True)
    reviewed_at: Mapped[date | None] = mapped_column(Date, nullable=True)


class CarePlan(OperationalMixin, Base):
    __tablename__ = "care_plans"
    __table_args__ = (
        CheckConstraint("goal_area IN ('Education', 'Health', 'Behavior', 'Emotional Support', 'Family Reunification', 'Legal', 'Life Skills', 'General Welfare')", name="ck_care_plans_goal_area"),
        CheckConstraint("status IN ('Active', 'Completed', 'On Hold', 'Cancelled')", name="ck_care_plans_status"),
        CheckConstraint("plan_end_date IS NULL OR plan_end_date >= plan_start_date", name="ck_care_plans_dates"),
        Index("ix_care_plans_child_status", "child_id", "status"),
        Index("ix_care_plans_plan_start_date", "plan_start_date"),
        Index("uq_care_plans_active_goal", "child_id", "goal_area", unique=True,
              postgresql_where=text("status = 'Active' AND deleted_at IS NULL"),
              sqlite_where=text("status = 'Active' AND deleted_at IS NULL")),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    child_id: Mapped[int] = mapped_column(ForeignKey("children.id", ondelete="RESTRICT"), index=True)
    case_profile_id: Mapped[int | None] = mapped_column(ForeignKey("child_case_profiles.id", ondelete="RESTRICT"), nullable=True, index=True)
    plan_title: Mapped[str] = mapped_column(String(255))
    plan_start_date: Mapped[date] = mapped_column(Date)
    plan_end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    goal_area: Mapped[str] = mapped_column(String(30), index=True)
    goals: Mapped[str] = mapped_column(Text)
    planned_actions: Mapped[str | None] = mapped_column(Text, nullable=True)
    responsible_person: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(15), index=True)
    progress_notes: Mapped[str | None] = mapped_column(Text, nullable=True)


class CaseReview(OperationalMixin, Base):
    __tablename__ = "case_reviews"
    __table_args__ = (
        CheckConstraint("review_type IN ('Monthly', 'Quarterly', 'Annual', 'Special', 'Emergency')", name="ck_case_reviews_type"),
        CheckConstraint("status IN ('Completed', 'Pending', 'Cancelled')", name="ck_case_reviews_status"),
        CheckConstraint("next_review_date IS NULL OR next_review_date >= review_date", name="ck_case_reviews_next_date"),
        Index("ix_case_reviews_child_date", "child_id", "review_date"),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    child_id: Mapped[int] = mapped_column(ForeignKey("children.id", ondelete="RESTRICT"), index=True)
    case_profile_id: Mapped[int | None] = mapped_column(ForeignKey("child_case_profiles.id", ondelete="RESTRICT"), nullable=True, index=True)
    review_date: Mapped[date] = mapped_column(Date, index=True)
    review_type: Mapped[str] = mapped_column(String(15))
    participants: Mapped[str | None] = mapped_column(Text, nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    decisions: Mapped[str | None] = mapped_column(Text, nullable=True)
    next_review_date: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(15), index=True)
