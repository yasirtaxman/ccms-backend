"""Add RBAC integrity and audit trail.

Revision ID: 7c13f21a934e
Revises: 2b9a9c01b4d8
Create Date: 2026-06-20
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "7c13f21a934e"
down_revision: Union[str, Sequence[str], None] = "2b9a9c01b4d8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Remove legacy duplicate assignments before enforcing idempotency.
    op.execute(
        sa.text(
            """
            DELETE FROM user_roles AS duplicate
            USING user_roles AS keeper
            WHERE duplicate.user_id = keeper.user_id
              AND duplicate.role_id = keeper.role_id
              AND duplicate.id > keeper.id
            """
        )
    )
    op.create_unique_constraint(
        "uq_user_roles_user_role", "user_roles", ["user_id", "role_id"]
    )

    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("action", sa.String(length=20), nullable=False),
        sa.Column("module", sa.String(length=30), nullable=False),
        sa.Column("record_id", sa.Integer(), nullable=True),
        sa.Column("old_values", sa.JSON(), nullable=True),
        sa.Column("new_values", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_audit_logs_user_id", "audit_logs", ["user_id"])
    op.create_index(
        "ix_audit_logs_module_record_id", "audit_logs", ["module", "record_id"]
    )
    op.create_index("ix_audit_logs_created_at", "audit_logs", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_audit_logs_created_at", table_name="audit_logs")
    op.drop_index("ix_audit_logs_module_record_id", table_name="audit_logs")
    op.drop_index("ix_audit_logs_user_id", table_name="audit_logs")
    op.drop_table("audit_logs")
    op.drop_constraint("uq_user_roles_user_role", "user_roles", type_="unique")
