from datetime import UTC, date, datetime

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, Index, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


def utc_now() -> datetime:
    return datetime.now(UTC)


class EducationRecord(Base):
    __tablename__ = "education_records"
    __table_args__ = (
        CheckConstraint(
            "status IN ('Studying', 'Completed', 'Dropped', 'Transferred')",
            name="ck_education_records_status",
        ),
        CheckConstraint("end_date IS NULL OR end_date >= start_date", name="ck_education_records_dates"),
        Index("ix_education_records_child_status", "child_id", "status"),
        Index("ix_education_records_school_year", "school_id", "academic_year"),
        Index(
            "uq_education_records_active_child",
            "child_id",
            unique=True,
            postgresql_where=text("status = 'Studying'"),
            sqlite_where=text("status = 'Studying'"),
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    child_id: Mapped[int] = mapped_column(ForeignKey("children.id", ondelete="RESTRICT"), index=True)
    school_id: Mapped[int] = mapped_column(ForeignKey("schools.id", ondelete="RESTRICT"), index=True)
    admission_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    class_level: Mapped[str] = mapped_column(String(50))
    academic_year: Mapped[str] = mapped_column(String(20))
    start_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(15), default="Studying")
    remarks: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    updated_by: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)
