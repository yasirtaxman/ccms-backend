"""add organization profile

Revision ID: d12f4a6b8c90
Revises: c11d8f2b704a
Create Date: 2026-06-23 12:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "d12f4a6b8c90"
down_revision: str | None = "c11d8f2b704a"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "organization_profiles",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("organization_name", sa.String(length=255), nullable=False),
        sa.Column("short_name", sa.String(length=80), nullable=False),
        sa.Column("logo_path", sa.String(length=500), nullable=True),
        sa.Column("address", sa.Text(), nullable=True),
        sa.Column("city", sa.String(length=120), nullable=True),
        sa.Column("district", sa.String(length=120), nullable=True),
        sa.Column("province", sa.String(length=120), nullable=True),
        sa.Column("country", sa.String(length=120), nullable=True),
        sa.Column("phone", sa.String(length=80), nullable=True),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("website", sa.String(length=255), nullable=True),
        sa.Column("registration_no", sa.String(length=120), nullable=True),
        sa.Column("ntn_or_tax_no", sa.String(length=120), nullable=True),
        sa.Column("report_footer_text", sa.String(length=500), nullable=True),
        sa.Column("report_watermark_text", sa.String(length=120), nullable=True),
        sa.Column("primary_color", sa.String(length=20), nullable=True),
        sa.Column("secondary_color", sa.String(length=20), nullable=True),
        sa.Column("authorized_signatory_name", sa.String(length=255), nullable=True),
        sa.Column("authorized_signatory_designation", sa.String(length=255), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("organization_profiles")
