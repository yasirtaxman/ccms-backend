from datetime import UTC, date, datetime

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


def utc_now() -> datetime:
    return datetime.now(UTC)


class Vaccination(Base):
    __tablename__ = "vaccinations"
    __table_args__ = (
        CheckConstraint("dose_number > 0", name="ck_vaccinations_dose_positive"),
        CheckConstraint(
            "next_due_date IS NULL OR next_due_date >= vaccination_date",
            name="ck_vaccinations_due_date",
        ),
        Index("ix_vaccinations_child_due", "child_id", "next_due_date"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    child_id: Mapped[int] = mapped_column(
        ForeignKey("children.id", ondelete="RESTRICT"), index=True
    )
    vaccine_name: Mapped[str] = mapped_column(String(255))
    dose_number: Mapped[int] = mapped_column(Integer)
    vaccination_date: Mapped[date] = mapped_column(Date)
    next_due_date: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)
    administered_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    hospital_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    remarks: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    updated_by: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )
