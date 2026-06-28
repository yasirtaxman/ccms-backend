"""add behavior support plans

Revision ID: g15b7d9e3f21
Revises: f14a6c8d2e10
Create Date: 2026-06-28 15:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "g15b7d9e3f21"
down_revision: str | None = "f14a6c8d2e10"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

PERMISSIONS = [
    "development.support_plan.view", "development.support_plan.create", "development.support_plan.generate",
    "development.support_plan.update", "development.support_plan.activate", "development.support_plan.review",
    "development.support_plan.complete", "development.support_plan.close", "development.support_plan.cancel",
    "development.support_plan.delete", "development.support_plan.export", "development.support_plan.notes.view",
    "development.support_plan.notes.create", "development.support_plan.notes.update", "development.support_plan.notes.delete",
    "development.support_plan.sensitive.view",
]


def add_permission(conn, name: str) -> None:
    module, action = name.rsplit(".", 1)
    conn.execute(sa.text("INSERT INTO permissions (name,module,action,description) SELECT :name,:module,:action,:description WHERE NOT EXISTS (SELECT 1 FROM permissions WHERE name=:name)"), {"name": name, "module": module, "action": action, "description": f"{action.replace('_',' ').title()} {module.replace('.',' ')}"})


def grant(conn, role: str, names: list[str]) -> None:
    role_id = conn.execute(sa.text("SELECT id FROM roles WHERE name=:name"), {"name": role}).scalar()
    if not role_id:
        return
    for name in names:
        permission_id = conn.execute(sa.text("SELECT id FROM permissions WHERE name=:name"), {"name": name}).scalar()
        if permission_id:
            conn.execute(sa.text("INSERT INTO role_permissions (role_id,permission_id) SELECT :role_id,:permission_id WHERE NOT EXISTS (SELECT 1 FROM role_permissions WHERE role_id=:role_id AND permission_id=:permission_id)"), {"role_id": role_id, "permission_id": permission_id})


def upgrade() -> None:
    op.create_table(
        "child_behavior_support_plans",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("child_id", sa.Integer(), nullable=False),
        sa.Column("plan_code", sa.String(length=80), nullable=False),
        sa.Column("plan_title", sa.String(length=255), nullable=False),
        sa.Column("plan_type", sa.String(length=50), nullable=False),
        sa.Column("plan_status", sa.String(length=40), nullable=False),
        sa.Column("priority_level", sa.String(length=40), nullable=False),
        sa.Column("identified_behavior", sa.Text(), nullable=True),
        sa.Column("behavior_description", sa.Text(), nullable=True),
        sa.Column("possible_triggers", sa.Text(), nullable=True),
        sa.Column("known_patterns", sa.Text(), nullable=True),
        sa.Column("time_location_context", sa.Text(), nullable=True),
        sa.Column("replacement_positive_behavior", sa.Text(), nullable=True),
        sa.Column("prevention_strategies", sa.Text(), nullable=True),
        sa.Column("staff_response_plan", sa.Text(), nullable=True),
        sa.Column("de_escalation_steps", sa.Text(), nullable=True),
        sa.Column("positive_reinforcement_plan", sa.Text(), nullable=True),
        sa.Column("environment_adjustments", sa.Text(), nullable=True),
        sa.Column("communication_support", sa.Text(), nullable=True),
        sa.Column("learning_support", sa.Text(), nullable=True),
        sa.Column("social_support", sa.Text(), nullable=True),
        sa.Column("counselor_recommendations", sa.Text(), nullable=True),
        sa.Column("guardian_communication_notes", sa.Text(), nullable=True),
        sa.Column("start_date", sa.Date(), nullable=True),
        sa.Column("review_date", sa.Date(), nullable=True),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("created_from_observation_id", sa.Integer(), nullable=True),
        sa.Column("created_from_ai_summary_id", sa.Integer(), nullable=True),
        sa.Column("responsible_staff_id", sa.Integer(), nullable=True),
        sa.Column("counselor_id", sa.Integer(), nullable=True),
        sa.Column("approved_by_user_id", sa.Integer(), nullable=True),
        sa.Column("progress_summary", sa.Text(), nullable=True),
        sa.Column("review_outcome", sa.Text(), nullable=True),
        sa.Column("closure_reason", sa.Text(), nullable=True),
        sa.Column("is_sensitive", sa.Boolean(), nullable=False),
        sa.Column("internal_notes", sa.Text(), nullable=True),
        sa.Column("created_by_user_id", sa.Integer(), nullable=False),
        sa.Column("updated_by_user_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["approved_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["child_id"], ["children.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["counselor_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["created_from_ai_summary_id"], ["child_development_ai_summaries.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["created_from_observation_id"], ["child_development_observations.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["responsible_staff_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["updated_by_user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("plan_code"),
    )
    for column in ["child_id", "plan_code", "plan_type", "plan_status", "priority_level", "start_date", "review_date"]:
        op.create_index(f"ix_child_behavior_support_plans_{column}", "child_behavior_support_plans", [column])
    op.create_table(
        "child_behavior_support_plan_notes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("plan_id", sa.Integer(), nullable=False),
        sa.Column("child_id", sa.Integer(), nullable=False),
        sa.Column("note_date", sa.Date(), nullable=False),
        sa.Column("note_type", sa.String(length=50), nullable=False),
        sa.Column("progress_note", sa.Text(), nullable=True),
        sa.Column("staff_action_taken", sa.Text(), nullable=True),
        sa.Column("child_response", sa.Text(), nullable=True),
        sa.Column("follow_up_required", sa.Boolean(), nullable=False),
        sa.Column("next_step", sa.Text(), nullable=True),
        sa.Column("created_by_user_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["child_id"], ["children.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["plan_id"], ["child_behavior_support_plans.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in ["plan_id", "child_id", "note_date", "note_type"]:
        op.create_index(f"ix_child_behavior_support_plan_notes_{column}", "child_behavior_support_plan_notes", [column])
    conn = op.get_bind()
    for permission in PERMISSIONS:
        add_permission(conn, permission)
    manager = [p for p in PERMISSIONS if p not in {"development.support_plan.delete", "development.support_plan.sensitive.view"}]
    counselor = [p for p in PERMISSIONS if p not in {"development.support_plan.activate", "development.support_plan.close", "development.support_plan.cancel", "development.support_plan.delete"}]
    grant(conn, "Manager", manager)
    grant(conn, "Counselor", counselor)
    grant(conn, "Warden", ["development.support_plan.view", "development.support_plan.notes.create"])
    grant(conn, "Data Entry Operator", ["development.support_plan.view", "development.support_plan.create", "development.support_plan.notes.create"])
    grant(conn, "Viewer", ["development.support_plan.view"])


def downgrade() -> None:
    for column in ["note_type", "note_date", "child_id", "plan_id"]:
        op.drop_index(f"ix_child_behavior_support_plan_notes_{column}", table_name="child_behavior_support_plan_notes")
    op.drop_table("child_behavior_support_plan_notes")
    for column in ["review_date", "start_date", "priority_level", "plan_status", "plan_type", "plan_code", "child_id"]:
        op.drop_index(f"ix_child_behavior_support_plans_{column}", table_name="child_behavior_support_plans")
    op.drop_table("child_behavior_support_plans")
