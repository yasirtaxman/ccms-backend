"""Add accommodation hierarchy and historical bed allocations.

Revision ID: a3c91e5d7b20
Revises: f84c0d9a217e
Create Date: 2026-06-20
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a3c91e5d7b20"
down_revision: Union[str, Sequence[str], None] = "f84c0d9a217e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def operational_columns(*, soft_delete: bool = True) -> list[sa.Column]:
    columns = [
        sa.Column("organization_id", sa.Integer(), nullable=True),
        sa.Column("created_by", sa.Integer(), nullable=False),
        sa.Column("updated_by", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
    ]
    if soft_delete:
        columns.extend([
            sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("deleted_by", sa.Integer(), nullable=True),
        ])
    return columns


def audit_foreign_keys(*, soft_delete: bool = True) -> list[sa.ForeignKeyConstraint]:
    constraints = [
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["updated_by"], ["users.id"], ondelete="RESTRICT"),
    ]
    if soft_delete:
        constraints.append(sa.ForeignKeyConstraint(["deleted_by"], ["users.id"], ondelete="RESTRICT"))
    return constraints


def tracking_indexes(table: str, *, soft_delete: bool = True) -> None:
    op.create_index(f"ix_{table}_organization_id", table, ["organization_id"])
    if soft_delete:
        op.create_index(f"ix_{table}_deleted_at", table, ["deleted_at"])


def upgrade() -> None:
    op.create_table(
        "buildings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("building_code", sa.String(50), nullable=False),
        sa.Column("building_name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("gender_type", sa.String(10), nullable=False),
        sa.Column("status", sa.String(10), nullable=False),
        *operational_columns(),
        sa.CheckConstraint("gender_type IN ('Male', 'Female', 'Mixed')", name="ck_buildings_gender_type"),
        sa.CheckConstraint("status IN ('Active', 'Inactive')", name="ck_buildings_status"),
        sa.UniqueConstraint("building_code", name="uq_buildings_building_code"),
        *audit_foreign_keys(),
    )
    op.create_index("ix_buildings_building_code", "buildings", ["building_code"])
    tracking_indexes("buildings")

    op.create_table(
        "blocks",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("building_id", sa.Integer(), nullable=False),
        sa.Column("block_code", sa.String(50), nullable=False),
        sa.Column("block_name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(10), nullable=False),
        *operational_columns(),
        sa.CheckConstraint("status IN ('Active', 'Inactive')", name="ck_blocks_status"),
        sa.ForeignKeyConstraint(["building_id"], ["buildings.id"], ondelete="RESTRICT"),
        sa.UniqueConstraint("building_id", "block_code", name="uq_blocks_building_code"),
        *audit_foreign_keys(),
    )
    op.create_index("ix_blocks_building_id", "blocks", ["building_id"])
    tracking_indexes("blocks")

    op.create_table(
        "floors",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("block_id", sa.Integer(), nullable=False),
        sa.Column("floor_no", sa.Integer(), nullable=False),
        sa.Column("floor_name", sa.String(255), nullable=False),
        sa.Column("status", sa.String(10), nullable=False),
        *operational_columns(),
        sa.CheckConstraint("status IN ('Active', 'Inactive')", name="ck_floors_status"),
        sa.ForeignKeyConstraint(["block_id"], ["blocks.id"], ondelete="RESTRICT"),
        sa.UniqueConstraint("block_id", "floor_no", name="uq_floors_block_no"),
        *audit_foreign_keys(),
    )
    op.create_index("ix_floors_block_id", "floors", ["block_id"])
    tracking_indexes("floors")

    op.create_table(
        "rooms",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("floor_id", sa.Integer(), nullable=False),
        sa.Column("room_code", sa.String(50), nullable=False),
        sa.Column("room_name", sa.String(255), nullable=False),
        sa.Column("capacity", sa.Integer(), nullable=False),
        sa.Column("gender_type", sa.String(10), nullable=False),
        sa.Column("status", sa.String(10), nullable=False),
        *operational_columns(),
        sa.CheckConstraint("capacity > 0", name="ck_rooms_capacity_positive"),
        sa.CheckConstraint("gender_type IN ('Male', 'Female', 'Mixed')", name="ck_rooms_gender_type"),
        sa.CheckConstraint("status IN ('Active', 'Inactive')", name="ck_rooms_status"),
        sa.ForeignKeyConstraint(["floor_id"], ["floors.id"], ondelete="RESTRICT"),
        sa.UniqueConstraint("room_code", name="uq_rooms_room_code"),
        *audit_foreign_keys(),
    )
    op.create_index("ix_rooms_floor_id", "rooms", ["floor_id"])
    op.create_index("ix_rooms_room_code", "rooms", ["room_code"])
    tracking_indexes("rooms")

    op.create_table(
        "beds",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("room_id", sa.Integer(), nullable=False),
        sa.Column("bed_code", sa.String(50), nullable=False),
        sa.Column("bed_name", sa.String(255), nullable=False),
        sa.Column("status", sa.String(15), nullable=False),
        *operational_columns(),
        sa.CheckConstraint("status IN ('Vacant', 'Occupied', 'Reserved', 'Maintenance')", name="ck_beds_status"),
        sa.ForeignKeyConstraint(["room_id"], ["rooms.id"], ondelete="RESTRICT"),
        sa.UniqueConstraint("bed_code", name="uq_beds_bed_code"),
        *audit_foreign_keys(),
    )
    op.create_index("ix_beds_room_id", "beds", ["room_id"])
    op.create_index("ix_beds_bed_code", "beds", ["bed_code"])
    op.create_index("ix_beds_room_status", "beds", ["room_id", "status"])
    tracking_indexes("beds")

    op.create_table(
        "bed_allocations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("child_id", sa.Integer(), nullable=False),
        sa.Column("bed_id", sa.Integer(), nullable=False),
        sa.Column("allocation_date", sa.Date(), nullable=False),
        sa.Column("vacation_date", sa.Date(), nullable=True),
        sa.Column("allocation_reason", sa.Text(), nullable=True),
        sa.Column("vacation_reason", sa.Text(), nullable=True),
        sa.Column("status", sa.String(15), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        *operational_columns(soft_delete=False),
        sa.CheckConstraint("status IN ('Active', 'Transferred', 'Vacated')", name="ck_bed_allocations_status"),
        sa.CheckConstraint("vacation_date IS NULL OR vacation_date >= allocation_date", name="ck_bed_allocations_date_range"),
        sa.ForeignKeyConstraint(["child_id"], ["children.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["bed_id"], ["beds.id"], ondelete="RESTRICT"),
        *audit_foreign_keys(soft_delete=False),
    )
    op.create_index("ix_bed_allocations_child_id", "bed_allocations", ["child_id"])
    op.create_index("ix_bed_allocations_bed_id", "bed_allocations", ["bed_id"])
    op.create_index("ix_bed_allocations_child_history", "bed_allocations", ["child_id", "allocation_date"])
    op.create_index("ix_bed_allocations_bed_history", "bed_allocations", ["bed_id", "allocation_date"])
    op.create_index("ix_bed_allocations_organization_id", "bed_allocations", ["organization_id"])
    op.create_index("uq_bed_allocations_active_child", "bed_allocations", ["child_id"], unique=True, postgresql_where=sa.text("status = 'Active'"))
    op.create_index("uq_bed_allocations_active_bed", "bed_allocations", ["bed_id"], unique=True, postgresql_where=sa.text("status = 'Active'"))


def downgrade() -> None:
    op.drop_table("bed_allocations")
    op.drop_table("beds")
    op.drop_table("rooms")
    op.drop_table("floors")
    op.drop_table("blocks")
    op.drop_table("buildings")
