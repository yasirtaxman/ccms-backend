from datetime import UTC, date, datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, Index, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


def utc_now() -> datetime:
    return datetime.now(UTC)


class ExamResult(Base):
    __tablename__ = "exam_results"
    __table_args__ = (
        CheckConstraint(
            "exam_name IN ('Monthly', 'Quarterly', 'Midterm', 'Annual', 'Board')",
            name="ck_exam_results_name",
        ),
        CheckConstraint("total_marks > 0", name="ck_exam_results_total_marks"),
        CheckConstraint("obtained_marks >= 0 AND obtained_marks <= total_marks", name="ck_exam_results_marks"),
        CheckConstraint("percentage >= 0 AND percentage <= 100", name="ck_exam_results_percentage"),
        Index("ix_exam_results_record_date", "education_record_id", "exam_date"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    education_record_id: Mapped[int] = mapped_column(ForeignKey("education_records.id", ondelete="RESTRICT"), index=True)
    exam_name: Mapped[str] = mapped_column(String(20), index=True)
    exam_date: Mapped[date] = mapped_column(Date, index=True)
    total_marks: Mapped[Decimal] = mapped_column(Numeric(8, 2))
    obtained_marks: Mapped[Decimal] = mapped_column(Numeric(8, 2))
    percentage: Mapped[Decimal] = mapped_column(Numeric(5, 2))
    grade: Mapped[str | None] = mapped_column(String(10), nullable=True)
    position: Mapped[int | None] = mapped_column(Integer, nullable=True)
    remarks: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    updated_by: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)
