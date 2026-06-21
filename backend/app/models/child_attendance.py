from datetime import UTC, date, datetime, time
from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, Index, Integer, String, Text, Time, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

ATTENDANCE_STATUSES = (
    "Present", "Absent", "On Leave", "Medical Leave", "Home Visit",
    "School Activity", "Outside Activity", "Unauthorized Absence", "Missing",
)

class DailyChildAttendance(Base):
    __tablename__ = "daily_child_attendance"
    __table_args__ = (
        CheckConstraint("status IN ('Present','Absent','On Leave','Medical Leave','Home Visit','School Activity','Outside Activity','Unauthorized Absence','Missing')", name="ck_daily_child_attendance_status"),
        Index("ix_daily_child_attendance_child_id", "child_id"),
        Index("ix_daily_child_attendance_date", "attendance_date"),
        Index("ix_daily_child_attendance_status", "status"),
        Index("ix_daily_child_attendance_organization_id", "organization_id"),
        Index("uq_daily_child_attendance_active_child_date", "child_id", "attendance_date", unique=True, postgresql_where=text("deleted_at IS NULL"), sqlite_where=text("deleted_at IS NULL")),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    child_id: Mapped[int] = mapped_column(ForeignKey("children.id", ondelete="CASCADE"), nullable=False)
    attendance_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String(40), nullable=False)
    check_in_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    check_out_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    marked_by: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    remarks: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    updated_by: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC), nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    deleted_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    child: Mapped["Child"] = relationship()

from app.models.child import Child  # noqa: E402
