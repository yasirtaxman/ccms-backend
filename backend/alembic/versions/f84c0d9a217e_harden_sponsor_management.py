"""Harden sponsor tenancy readiness, history, privacy, and audit data.

Revision ID: f84c0d9a217e
Revises: e31a8d2f6b47
Create Date: 2026-06-20
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "f84c0d9a217e"
down_revision: Union[str, Sequence[str], None] = "e31a8d2f6b47"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("sponsors", sa.Column("organization_id", sa.Integer(), nullable=True))
    op.add_column(
        "sponsors", sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column("sponsors", sa.Column("deleted_by", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_sponsors_deleted_by_users",
        "sponsors",
        "users",
        ["deleted_by"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_index("ix_sponsors_organization_id", "sponsors", ["organization_id"])
    op.create_index("ix_sponsors_deleted_at", "sponsors", ["deleted_at"])

    op.add_column(
        "child_sponsorships",
        sa.Column("organization_id", sa.Integer(), nullable=True),
    )
    op.create_index(
        "ix_child_sponsorships_organization_id",
        "child_sponsorships",
        ["organization_id"],
    )

    op.alter_column(
        "audit_logs",
        "action",
        existing_type=sa.String(length=20),
        type_=sa.String(length=40),
        existing_nullable=False,
    )
    op.alter_column(
        "audit_logs",
        "old_values",
        existing_type=sa.JSON(),
        type_=postgresql.JSONB(astext_type=sa.Text()),
        existing_nullable=True,
        postgresql_using="old_values::jsonb",
    )
    op.alter_column(
        "audit_logs",
        "new_values",
        existing_type=sa.JSON(),
        type_=postgresql.JSONB(astext_type=sa.Text()),
        existing_nullable=True,
        postgresql_using="new_values::jsonb",
    )

    op.execute("CREATE EXTENSION IF NOT EXISTS btree_gist")
    op.execute(
        """
        CREATE FUNCTION ccms_prevent_sponsorship_sponsor_change()
        RETURNS trigger
        LANGUAGE plpgsql
        AS $$
        BEGIN
            IF NEW.sponsor_id IS DISTINCT FROM OLD.sponsor_id THEN
                RAISE EXCEPTION 'sponsor_id is immutable after sponsorship creation'
                    USING ERRCODE = 'integrity_constraint_violation';
            END IF;
            RETURN NEW;
        END;
        $$
        """
    )
    op.execute(
        """
        CREATE TRIGGER trg_child_sponsorships_immutable_sponsor
        BEFORE UPDATE OF sponsor_id ON child_sponsorships
        FOR EACH ROW
        EXECUTE FUNCTION ccms_prevent_sponsorship_sponsor_change()
        """
    )
    op.execute(
        """
        ALTER TABLE child_sponsorships
        ADD CONSTRAINT excl_child_sponsorships_period
        EXCLUDE USING gist (
            child_id WITH =,
            sponsor_id WITH =,
            daterange(
                start_date,
                COALESCE(end_date, 'infinity'::date),
                '[]'
            ) WITH &&
        )
        """
    )


def downgrade() -> None:
    op.drop_constraint("excl_child_sponsorships_period", "child_sponsorships")
    op.execute(
        "DROP TRIGGER trg_child_sponsorships_immutable_sponsor ON child_sponsorships"
    )
    op.execute("DROP FUNCTION ccms_prevent_sponsorship_sponsor_change()")

    # The earlier schema cannot represent the dedicated long event name.
    op.execute(
        """
        UPDATE audit_logs
        SET action = 'UPDATE'
        WHERE action = 'SPONSORSHIP_STATUS_CHANGE'
        """
    )
    op.alter_column(
        "audit_logs",
        "new_values",
        existing_type=postgresql.JSONB(astext_type=sa.Text()),
        type_=sa.JSON(),
        existing_nullable=True,
        postgresql_using="new_values::json",
    )
    op.alter_column(
        "audit_logs",
        "old_values",
        existing_type=postgresql.JSONB(astext_type=sa.Text()),
        type_=sa.JSON(),
        existing_nullable=True,
        postgresql_using="old_values::json",
    )
    op.alter_column(
        "audit_logs",
        "action",
        existing_type=sa.String(length=40),
        type_=sa.String(length=20),
        existing_nullable=False,
    )

    op.drop_index(
        "ix_child_sponsorships_organization_id",
        table_name="child_sponsorships",
    )
    op.drop_column("child_sponsorships", "organization_id")

    op.drop_index("ix_sponsors_deleted_at", table_name="sponsors")
    op.drop_index("ix_sponsors_organization_id", table_name="sponsors")
    op.drop_constraint("fk_sponsors_deleted_by_users", "sponsors", type_="foreignkey")
    op.drop_column("sponsors", "deleted_by")
    op.drop_column("sponsors", "deleted_at")
    op.drop_column("sponsors", "organization_id")
