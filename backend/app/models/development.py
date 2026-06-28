from datetime import UTC, date, datetime
from typing import Any

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


def now() -> datetime:
    return datetime.now(UTC)


class DevelopmentIndicator(Base):
    __tablename__ = "development_indicators"

    id: Mapped[int] = mapped_column(primary_key=True)
    indicator_code: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    indicator_name: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(150), index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    input_type: Mapped[str] = mapped_column(String(40), nullable=False)
    options_json: Mapped[list[Any] | dict[str, Any] | None] = mapped_column(JSON().with_variant(JSONB, "postgresql"), nullable=True)
    is_required: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_sensitive: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, onupdate=now, nullable=False)

    responses: Mapped[list["ChildDevelopmentObservationResponse"]] = relationship(back_populates="indicator")


class ChildDevelopmentObservation(Base):
    __tablename__ = "child_development_observations"

    id: Mapped[int] = mapped_column(primary_key=True)
    child_id: Mapped[int] = mapped_column(ForeignKey("children.id", ondelete="RESTRICT"), index=True)
    observation_date: Mapped[date] = mapped_column(Date, index=True)
    observation_period_start: Mapped[date | None] = mapped_column(Date, nullable=True)
    observation_period_end: Mapped[date | None] = mapped_column(Date, nullable=True)
    observation_frequency: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    observed_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    observer_role: Mapped[str | None] = mapped_column(String(100), nullable=True)
    review_status: Mapped[str] = mapped_column(String(40), default="Draft", nullable=False, index=True)
    general_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    recommended_support: Mapped[str | None] = mapped_column(Text, nullable=True)
    private_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    urgent_flag: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    next_review_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    reviewed_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, onupdate=now, nullable=False)
    created_by_user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    updated_by_user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)

    responses: Mapped[list["ChildDevelopmentObservationResponse"]] = relationship(back_populates="observation", cascade="all, delete-orphan", lazy="selectin")


class ChildDevelopmentObservationResponse(Base):
    __tablename__ = "child_development_observation_responses"
    __table_args__ = (UniqueConstraint("observation_id", "indicator_id", name="uq_development_response_observation_indicator"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    observation_id: Mapped[int] = mapped_column(ForeignKey("child_development_observations.id", ondelete="CASCADE"), index=True)
    indicator_id: Mapped[int] = mapped_column(ForeignKey("development_indicators.id", ondelete="RESTRICT"), index=True)
    value_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    value_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    value_boolean: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    value_json: Mapped[list[Any] | dict[str, Any] | None] = mapped_column(JSON().with_variant(JSONB, "postgresql"), nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, onupdate=now, nullable=False)

    observation: Mapped[ChildDevelopmentObservation] = relationship(back_populates="responses")
    indicator: Mapped[DevelopmentIndicator] = relationship(back_populates="responses", lazy="selectin")


class ChildDevelopmentAISummary(Base):
    __tablename__ = "child_development_ai_summaries"

    id: Mapped[int] = mapped_column(primary_key=True)
    child_id: Mapped[int] = mapped_column(ForeignKey("children.id", ondelete="RESTRICT"), index=True)
    summary_period_month: Mapped[int] = mapped_column(Integer, index=True)
    summary_period_year: Mapped[int] = mapped_column(Integer, index=True)
    summary_type: Mapped[str] = mapped_column(String(80), default="Monthly Development Intelligence", nullable=False, index=True)
    overall_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    positive_strengths_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    support_needs_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    talent_interest_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    behavior_trend_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    emotional_wellbeing_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    learning_behavior_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    social_behavior_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    risk_attention_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    recommended_staff_actions: Mapped[str | None] = mapped_column(Text, nullable=True)
    recommended_counselor_actions: Mapped[str | None] = mapped_column(Text, nullable=True)
    next_review_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    trend_status: Mapped[str] = mapped_column(String(40), default="Not Enough Data", nullable=False, index=True)
    attention_level: Mapped[str] = mapped_column(String(40), default="Low", nullable=False, index=True)
    approval_status: Mapped[str] = mapped_column(String(40), default="Generated", nullable=False, index=True)
    generated_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    reviewed_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    approved_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, nullable=False)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    source_observation_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    source_date_from: Mapped[date | None] = mapped_column(Date, nullable=True)
    source_date_to: Mapped[date | None] = mapped_column(Date, nullable=True)
    is_ai_generated: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_sensitive: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    internal_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, onupdate=now, nullable=False)
