from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Integer, Numeric, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


def utc_now() -> datetime:
    return datetime.now(UTC)


class Attendance(Base):
    __tablename__ = "attendance"
    __table_args__ = (
        CheckConstraint("month >= 1 AND month <= 12", name="ck_attendance_month"),
        CheckConstraint("year >= 1900 AND year <= 2200", name="ck_attendance_year"),
        CheckConstraint("total_days > 0", name="ck_attendance_total_days"),
        CheckConstraint("present_days >= 0 AND absent_days >= 0", name="ck_attendance_nonnegative"),
        CheckConstraint("present_days + absent_days = total_days", name="ck_attendance_day_totals"),
        CheckConstraint("attendance_percentage >= 0 AND attendance_percentage <= 100", name="ck_attendance_percentage"),
        UniqueConstraint("education_record_id", "month", "year", name="uq_attendance_record_month_year"),
        Index("ix_attendance_record_period", "education_record_id", "year", "month"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    education_record_id: Mapped[int] = mapped_column(ForeignKey("education_records.id", ondelete="RESTRICT"), index=True)
    month: Mapped[int] = mapped_column(Integer)
    year: Mapped[int] = mapped_column(Integer)
    total_days: Mapped[int] = mapped_column(Integer)
    present_days: Mapped[int] = mapped_column(Integer)
    absent_days: Mapped[int] = mapped_column(Integer)
    attendance_percentage: Mapped[Decimal] = mapped_column(Numeric(5, 2))
    remarks: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    updated_by: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)
