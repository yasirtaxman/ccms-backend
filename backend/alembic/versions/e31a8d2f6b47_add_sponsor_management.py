"""Add sponsor management and historical child sponsorships.

Revision ID: e31a8d2f6b47
Revises: 7c13f21a934e
Create Date: 2026-06-20
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e31a8d2f6b47"
down_revision: Union[str, Sequence[str], None] = "7c13f21a934e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "sponsors",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("sponsor_code", sa.String(length=50), nullable=False),
        sa.Column("sponsor_type", sa.String(length=20), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("organization_name", sa.String(length=255), nullable=True),
        sa.Column("mobile", sa.String(length=30), nullable=False),
        sa.Column("alternate_mobile", sa.String(length=30), nullable=True),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("cnic_passport", sa.String(length=50), nullable=True),
        sa.Column("address", sa.Text(), nullable=True),
        sa.Column("city", sa.String(length=100), nullable=True),
        sa.Column("district", sa.String(length=100), nullable=True),
        sa.Column("province", sa.String(length=100), nullable=True),
        sa.Column("country", sa.String(length=100), nullable=False),
        sa.Column("occupation", sa.String(length=150), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("remarks", sa.Text(), nullable=True),
        sa.Column("created_by", sa.Integer(), nullable=False),
        sa.Column("updated_by", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "sponsor_type IN ('Individual', 'Organization', 'Foundation', 'Corporate')",
            name="ck_sponsors_sponsor_type",
        ),
        sa.CheckConstraint(
            "status IN ('Active', 'Inactive', 'Blocked')",
            name="ck_sponsors_status",
        ),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["updated_by"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("sponsor_code", name="uq_sponsors_sponsor_code"),
    )
    op.create_index("ix_sponsors_sponsor_code", "sponsors", ["sponsor_code"])
    op.create_index("ix_sponsors_status_type", "sponsors", ["status", "sponsor_type"])
    op.create_index("ix_sponsors_name", "sponsors", ["full_name"])
    op.create_index("ix_sponsors_mobile", "sponsors", ["mobile"])
    op.create_index("ix_sponsors_email", "sponsors", ["email"])

    op.create_table(
        "child_sponsorships",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("child_id", sa.Integer(), nullable=False),
        sa.Column("sponsor_id", sa.Integer(), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("sponsorship_type", sa.String(length=20), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_by", sa.Integer(), nullable=False),
        sa.Column("updated_by", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "status IN ('Active', 'Completed', 'Cancelled', 'Suspended')",
            name="ck_child_sponsorships_status",
        ),
        sa.CheckConstraint(
            "sponsorship_type IN ('Full', 'Partial', 'Education', 'Medical', 'General')",
            name="ck_child_sponsorships_type",
        ),
        sa.CheckConstraint(
            "end_date IS NULL OR end_date >= start_date",
            name="ck_child_sponsorships_date_range",
        ),
        sa.ForeignKeyConstraint(["child_id"], ["children.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["sponsor_id"], ["sponsors.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["updated_by"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_child_sponsorships_child_id", "child_sponsorships", ["child_id"])
    op.create_index("ix_child_sponsorships_sponsor_id", "child_sponsorships", ["sponsor_id"])
    op.create_index(
        "ix_child_sponsorships_child_status", "child_sponsorships", ["child_id", "status"]
    )
    op.create_index(
        "ix_child_sponsorships_sponsor_status", "child_sponsorships", ["sponsor_id", "status"]
    )
    op.create_index(
        "ix_child_sponsorships_dates", "child_sponsorships", ["start_date", "end_date"]
    )


def downgrade() -> None:
    op.drop_index("ix_child_sponsorships_dates", table_name="child_sponsorships")
    op.drop_index("ix_child_sponsorships_sponsor_status", table_name="child_sponsorships")
    op.drop_index("ix_child_sponsorships_child_status", table_name="child_sponsorships")
    op.drop_index("ix_child_sponsorships_sponsor_id", table_name="child_sponsorships")
    op.drop_index("ix_child_sponsorships_child_id", table_name="child_sponsorships")
    op.drop_table("child_sponsorships")

    op.drop_index("ix_sponsors_email", table_name="sponsors")
    op.drop_index("ix_sponsors_mobile", table_name="sponsors")
    op.drop_index("ix_sponsors_name", table_name="sponsors")
    op.drop_index("ix_sponsors_status_type", table_name="sponsors")
    op.drop_index("ix_sponsors_sponsor_code", table_name="sponsors")
    op.drop_table("sponsors")
