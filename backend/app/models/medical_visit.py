from datetime import UTC, date, datetime

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


def utc_now() -> datetime:
    return datetime.now(UTC)


class MedicalVisit(Base):
    __tablename__ = "medical_visits"
    __table_args__ = (
        CheckConstraint(
            "visit_type IN ('Routine', 'Emergency', 'Specialist', 'Follow-up')",
            name="ck_medical_visits_type",
        ),
        Index("ix_medical_visits_child_date", "child_id", "visit_date"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    child_id: Mapped[int] = mapped_column(
        ForeignKey("children.id", ondelete="RESTRICT"), index=True
    )
    visit_date: Mapped[date] = mapped_column(Date, index=True)
    doctor_name: Mapped[str] = mapped_column(String(255))
    hospital_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    visit_type: Mapped[str] = mapped_column(String(20))
    symptoms: Mapped[str | None] = mapped_column(Text, nullable=True)
    diagnosis: Mapped[str | None] = mapped_column(Text, nullable=True)
    treatment: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    updated_by: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )
