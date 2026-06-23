from datetime import UTC, datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


def utc_now() -> datetime:
    return datetime.now(UTC)


class School(Base):
    __tablename__ = "schools"
    __table_args__ = (
        CheckConstraint(
            "school_type IN ('Government', 'Private', 'Madrassa', 'Technical', 'College', 'University')",
            name="ck_schools_type",
        ),
        CheckConstraint("status IN ('Active', 'Inactive')", name="ck_schools_status"),
        Index("ix_schools_status_type", "status", "school_type"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    school_code: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    school_name: Mapped[str] = mapped_column(String(255))
    school_type: Mapped[str] = mapped_column(String(20))
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    district: Mapped[str | None] = mapped_column(String(100), nullable=True)
    province: Mapped[str | None] = mapped_column(String(100), nullable=True)
    contact_person: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(30), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(10), default="Active")
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    updated_by: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)
