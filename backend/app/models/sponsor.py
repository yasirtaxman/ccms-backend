from datetime import UTC, date, datetime

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


def utc_now() -> datetime:
    return datetime.now(UTC)


class Sponsor(Base):
    __tablename__ = "sponsors"
    __table_args__ = (
        CheckConstraint(
            "sponsor_type IN ('Individual', 'Organization', 'Foundation', 'Corporate')",
            name="ck_sponsors_sponsor_type",
        ),
        CheckConstraint(
            "status IN ('Active', 'Inactive', 'Blocked')",
            name="ck_sponsors_status",
        ),
        Index("ix_sponsors_status_type", "status", "sponsor_type"),
        Index("ix_sponsors_name", "full_name"),
        Index("ix_sponsors_mobile", "mobile"),
        Index("ix_sponsors_email", "email"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    sponsor_code: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    sponsor_type: Mapped[str] = mapped_column(String(20))
    full_name: Mapped[str] = mapped_column(String(255))
    organization_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    mobile: Mapped[str] = mapped_column(String(30))
    alternate_mobile: Mapped[str | None] = mapped_column(String(30), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    cnic_passport: Mapped[str | None] = mapped_column(String(50), nullable=True)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    district: Mapped[str | None] = mapped_column(String(100), nullable=True)
    province: Mapped[str | None] = mapped_column(String(100), nullable=True)
    country: Mapped[str] = mapped_column(String(100), default="Pakistan")
    occupation: Mapped[str | None] = mapped_column(String(150), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="Active")
    remarks: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    updated_by: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
    deleted_by: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )

    sponsorships: Mapped[list["ChildSponsorship"]] = relationship(
        back_populates="sponsor"
    )


class ChildSponsorship(Base):
    __tablename__ = "child_sponsorships"
    __table_args__ = (
        CheckConstraint(
            "status IN ('Active', 'Completed', 'Cancelled', 'Suspended')",
            name="ck_child_sponsorships_status",
        ),
        CheckConstraint(
            "sponsorship_type IN ('Full', 'Partial', 'Education', 'Medical', 'General')",
            name="ck_child_sponsorships_type",
        ),
        CheckConstraint(
            "end_date IS NULL OR end_date >= start_date",
            name="ck_child_sponsorships_date_range",
        ),
        Index("ix_child_sponsorships_child_status", "child_id", "status"),
        Index("ix_child_sponsorships_sponsor_status", "sponsor_id", "status"),
        Index("ix_child_sponsorships_dates", "start_date", "end_date"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    child_id: Mapped[int] = mapped_column(
        ForeignKey("children.id", ondelete="RESTRICT"), index=True
    )
    sponsor_id: Mapped[int] = mapped_column(
        ForeignKey("sponsors.id", ondelete="RESTRICT"), index=True
    )
    start_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="Active")
    sponsorship_type: Mapped[str] = mapped_column(String(20))
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    updated_by: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )

    sponsor: Mapped[Sponsor] = relationship(back_populates="sponsorships")
    child: Mapped["Child"] = relationship(back_populates="sponsorships")


from app.models.child import Child  # noqa: E402
