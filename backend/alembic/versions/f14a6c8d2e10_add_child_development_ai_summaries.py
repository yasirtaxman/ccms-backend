"""add child development ai summaries

Revision ID: f14a6c8d2e10
Revises: e13a5b7c9d20
Create Date: 2026-06-28 14:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "f14a6c8d2e10"
down_revision: str | None = "e13a5b7c9d20"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


AI_PERMISSIONS = [
    "development.ai_summary.view",
    "development.ai_summary.generate",
    "development.ai_summary.update",
    "development.ai_summary.review",
    "development.ai_summary.approve",
    "development.ai_summary.reject",
    "development.ai_summary.delete",
    "development.ai_summary.export",
    "development.ai_summary.sensitive.view",
]


def _add_permission(conn, name: str) -> None:
    module, action = name.rsplit(".", 1)
    conn.execute(
        sa.text(
            "INSERT INTO permissions (name,module,action,description) "
            "SELECT :name,:module,:action,:description WHERE NOT EXISTS (SELECT 1 FROM permissions WHERE name=:name)"
        ),
        {"name": name, "module": module, "action": action, "description": f"{action.replace('_',' ').title()} {module.replace('.',' ')}"},
    )


def _grant(conn, role_name: str, names: list[str]) -> None:
    role_id = conn.execute(sa.text("SELECT id FROM roles WHERE name=:name"), {"name": role_name}).scalar()
    if not role_id:
        return
    for name in names:
        permission_id = conn.execute(sa.text("SELECT id FROM permissions WHERE name=:name"), {"name": name}).scalar()
        if permission_id:
            conn.execute(
                sa.text(
                    "INSERT INTO role_permissions (role_id,permission_id) "
                    "SELECT :role_id,:permission_id WHERE NOT EXISTS "
                    "(SELECT 1 FROM role_permissions WHERE role_id=:role_id AND permission_id=:permission_id)"
                ),
                {"role_id": role_id, "permission_id": permission_id},
            )


def upgrade() -> None:
    op.create_table(
        "child_development_ai_summaries",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("child_id", sa.Integer(), nullable=False),
        sa.Column("summary_period_month", sa.Integer(), nullable=False),
        sa.Column("summary_period_year", sa.Integer(), nullable=False),
        sa.Column("summary_type", sa.String(length=80), nullable=False),
        sa.Column("overall_summary", sa.Text(), nullable=True),
        sa.Column("positive_strengths_summary", sa.Text(), nullable=True),
        sa.Column("support_needs_summary", sa.Text(), nullable=True),
        sa.Column("talent_interest_summary", sa.Text(), nullable=True),
        sa.Column("behavior_trend_summary", sa.Text(), nullable=True),
        sa.Column("emotional_wellbeing_summary", sa.Text(), nullable=True),
        sa.Column("learning_behavior_summary", sa.Text(), nullable=True),
        sa.Column("social_behavior_summary", sa.Text(), nullable=True),
        sa.Column("risk_attention_summary", sa.Text(), nullable=True),
        sa.Column("recommended_staff_actions", sa.Text(), nullable=True),
        sa.Column("recommended_counselor_actions", sa.Text(), nullable=True),
        sa.Column("next_review_date", sa.Date(), nullable=True),
        sa.Column("trend_status", sa.String(length=40), nullable=False),
        sa.Column("attention_level", sa.String(length=40), nullable=False),
        sa.Column("approval_status", sa.String(length=40), nullable=False),
        sa.Column("generated_by_user_id", sa.Integer(), nullable=True),
        sa.Column("reviewed_by_user_id", sa.Integer(), nullable=True),
        sa.Column("approved_by_user_id", sa.Integer(), nullable=True),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("source_observation_count", sa.Integer(), nullable=False),
        sa.Column("source_date_from", sa.Date(), nullable=True),
        sa.Column("source_date_to", sa.Date(), nullable=True),
        sa.Column("is_ai_generated", sa.Boolean(), nullable=False),
        sa.Column("is_sensitive", sa.Boolean(), nullable=False),
        sa.Column("internal_notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["approved_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["child_id"], ["children.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["generated_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["reviewed_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in ["child_id", "summary_period_month", "summary_period_year", "summary_type", "trend_status", "attention_level", "approval_status"]:
        op.create_index(f"ix_child_development_ai_summaries_{column}", "child_development_ai_summaries", [column])
    conn = op.get_bind()
    for permission in AI_PERMISSIONS:
        _add_permission(conn, permission)
    _grant(conn, "Manager", [p for p in AI_PERMISSIONS if p != "development.ai_summary.sensitive.view"])
    _grant(conn, "Counselor", ["development.ai_summary.view", "development.ai_summary.generate", "development.ai_summary.update", "development.ai_summary.review", "development.ai_summary.export", "development.ai_summary.sensitive.view"])
    _grant(conn, "Viewer", ["development.ai_summary.view"])
    _grant(conn, "Data Entry Operator", ["development.ai_summary.view", "development.ai_summary.generate"])


def downgrade() -> None:
    for column in ["approval_status", "attention_level", "trend_status", "summary_type", "summary_period_year", "summary_period_month", "child_id"]:
        op.drop_index(f"ix_child_development_ai_summaries_{column}", table_name="child_development_ai_summaries")
    op.drop_table("child_development_ai_summaries")
