from datetime import UTC, date, datetime

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


def utc_now() -> datetime:
    return datetime.now(UTC)


class OperationalMixin:
    organization_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    updated_by: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)


class SoftDeleteMixin:
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    deleted_by: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=True
    )


class Building(OperationalMixin, SoftDeleteMixin, Base):
    __tablename__ = "buildings"
    __table_args__ = (
        CheckConstraint("gender_type IN ('Male', 'Female', 'Mixed')", name="ck_buildings_gender_type"),
        CheckConstraint("status IN ('Active', 'Inactive')", name="ck_buildings_status"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    building_code: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    building_name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    gender_type: Mapped[str] = mapped_column(String(10))
    status: Mapped[str] = mapped_column(String(10), default="Active")
    blocks: Mapped[list["Block"]] = relationship(back_populates="building")


class Block(OperationalMixin, SoftDeleteMixin, Base):
    __tablename__ = "blocks"
    __table_args__ = (
        CheckConstraint("status IN ('Active', 'Inactive')", name="ck_blocks_status"),
        UniqueConstraint("building_id", "block_code", name="uq_blocks_building_code"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    building_id: Mapped[int] = mapped_column(ForeignKey("buildings.id", ondelete="RESTRICT"), index=True)
    block_code: Mapped[str] = mapped_column(String(50))
    block_name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(10), default="Active")
    building: Mapped[Building] = relationship(back_populates="blocks")
    floors: Mapped[list["Floor"]] = relationship(back_populates="block")


class Floor(OperationalMixin, SoftDeleteMixin, Base):
    __tablename__ = "floors"
    __table_args__ = (
        CheckConstraint("status IN ('Active', 'Inactive')", name="ck_floors_status"),
        UniqueConstraint("block_id", "floor_no", name="uq_floors_block_no"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    block_id: Mapped[int] = mapped_column(ForeignKey("blocks.id", ondelete="RESTRICT"), index=True)
    floor_no: Mapped[int] = mapped_column(Integer)
    floor_name: Mapped[str] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(10), default="Active")
    block: Mapped[Block] = relationship(back_populates="floors")
    rooms: Mapped[list["Room"]] = relationship(back_populates="floor")


class Room(OperationalMixin, SoftDeleteMixin, Base):
    __tablename__ = "rooms"
    __table_args__ = (
        CheckConstraint("capacity > 0", name="ck_rooms_capacity_positive"),
        CheckConstraint("gender_type IN ('Male', 'Female', 'Mixed')", name="ck_rooms_gender_type"),
        CheckConstraint("status IN ('Active', 'Inactive')", name="ck_rooms_status"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    floor_id: Mapped[int] = mapped_column(ForeignKey("floors.id", ondelete="RESTRICT"), index=True)
    room_code: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    room_name: Mapped[str] = mapped_column(String(255))
    capacity: Mapped[int] = mapped_column(Integer)
    gender_type: Mapped[str] = mapped_column(String(10))
    status: Mapped[str] = mapped_column(String(10), default="Active")
    floor: Mapped[Floor] = relationship(back_populates="rooms")
    beds: Mapped[list["Bed"]] = relationship(back_populates="room")


class Bed(OperationalMixin, SoftDeleteMixin, Base):
    __tablename__ = "beds"
    __table_args__ = (
        CheckConstraint(
            "status IN ('Vacant', 'Occupied', 'Reserved', 'Maintenance')",
            name="ck_beds_status",
        ),
        Index("ix_beds_room_status", "room_id", "status"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    room_id: Mapped[int] = mapped_column(ForeignKey("rooms.id", ondelete="RESTRICT"), index=True)
    bed_code: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    bed_name: Mapped[str] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(15), default="Vacant")
    room: Mapped[Room] = relationship(back_populates="beds")
    allocations: Mapped[list["BedAllocation"]] = relationship(back_populates="bed")


class BedAllocation(OperationalMixin, Base):
    __tablename__ = "bed_allocations"
    __table_args__ = (
        CheckConstraint("status IN ('Active', 'Transferred', 'Vacated')", name="ck_bed_allocations_status"),
        CheckConstraint(
            "vacation_date IS NULL OR vacation_date >= allocation_date",
            name="ck_bed_allocations_date_range",
        ),
        Index(
            "uq_bed_allocations_active_child",
            "child_id",
            unique=True,
            postgresql_where=text("status = 'Active'"),
            sqlite_where=text("status = 'Active'"),
        ),
        Index(
            "uq_bed_allocations_active_bed",
            "bed_id",
            unique=True,
            postgresql_where=text("status = 'Active'"),
            sqlite_where=text("status = 'Active'"),
        ),
        Index("ix_bed_allocations_child_history", "child_id", "allocation_date"),
        Index("ix_bed_allocations_bed_history", "bed_id", "allocation_date"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    child_id: Mapped[int] = mapped_column(ForeignKey("children.id", ondelete="RESTRICT"), index=True)
    bed_id: Mapped[int] = mapped_column(ForeignKey("beds.id", ondelete="RESTRICT"), index=True)
    allocation_date: Mapped[date] = mapped_column(Date)
    vacation_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    allocation_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    vacation_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(15), default="Active")
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    bed: Mapped[Bed] = relationship(back_populates="allocations")
