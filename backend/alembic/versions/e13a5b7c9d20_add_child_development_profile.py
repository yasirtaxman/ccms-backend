"""add child development profile

Revision ID: e13a5b7c9d20
Revises: d12f4a6b8c90
Create Date: 2026-06-23 13:00:00.000000
"""

from collections.abc import Sequence
from datetime import datetime, timezone

import sqlalchemy as sa
from alembic import op

revision: str = "e13a5b7c9d20"
down_revision: str | None = "d12f4a6b8c90"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "development_indicators",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("indicator_code", sa.String(length=80), nullable=False),
        sa.Column("indicator_name", sa.String(length=255), nullable=False),
        sa.Column("category", sa.String(length=150), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("input_type", sa.String(length=40), nullable=False),
        sa.Column("options_json", sa.JSON(), nullable=True),
        sa.Column("is_required", sa.Boolean(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("is_sensitive", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("indicator_code"),
    )
    op.create_index("ix_development_indicators_indicator_code", "development_indicators", ["indicator_code"])
    op.create_index("ix_development_indicators_category", "development_indicators", ["category"])
    op.create_table(
        "child_development_observations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("child_id", sa.Integer(), nullable=False),
        sa.Column("observation_date", sa.Date(), nullable=False),
        sa.Column("observation_period_start", sa.Date(), nullable=True),
        sa.Column("observation_period_end", sa.Date(), nullable=True),
        sa.Column("observation_frequency", sa.String(length=40), nullable=False),
        sa.Column("observed_by_user_id", sa.Integer(), nullable=True),
        sa.Column("observer_role", sa.String(length=100), nullable=True),
        sa.Column("review_status", sa.String(length=40), nullable=False),
        sa.Column("general_summary", sa.Text(), nullable=True),
        sa.Column("recommended_support", sa.Text(), nullable=True),
        sa.Column("private_notes", sa.Text(), nullable=True),
        sa.Column("urgent_flag", sa.Boolean(), nullable=False),
        sa.Column("next_review_date", sa.Date(), nullable=True),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reviewed_by_user_id", sa.Integer(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by_user_id", sa.Integer(), nullable=False),
        sa.Column("updated_by_user_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["child_id"], ["children.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["observed_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["reviewed_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["updated_by_user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_child_development_observations_child_id", "child_development_observations", ["child_id"])
    op.create_index("ix_child_development_observations_observation_date", "child_development_observations", ["observation_date"])
    op.create_index("ix_child_development_observations_observation_frequency", "child_development_observations", ["observation_frequency"])
    op.create_index("ix_child_development_observations_review_status", "child_development_observations", ["review_status"])
    op.create_index("ix_child_development_observations_urgent_flag", "child_development_observations", ["urgent_flag"])
    op.create_table(
        "child_development_observation_responses",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("observation_id", sa.Integer(), nullable=False),
        sa.Column("indicator_id", sa.Integer(), nullable=False),
        sa.Column("value_text", sa.Text(), nullable=True),
        sa.Column("value_number", sa.Integer(), nullable=True),
        sa.Column("value_boolean", sa.Boolean(), nullable=True),
        sa.Column("value_json", sa.JSON(), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["indicator_id"], ["development_indicators.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["observation_id"], ["child_development_observations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("observation_id", "indicator_id", name="uq_development_response_observation_indicator"),
    )
    op.create_index("ix_child_development_observation_responses_observation_id", "child_development_observation_responses", ["observation_id"])
    op.create_index("ix_child_development_observation_responses_indicator_id", "child_development_observation_responses", ["indicator_id"])

    now = datetime.now(timezone.utc)
    permission_rows = []
    modules = {
        "development": ["view", "create", "update", "delete", "submit", "review", "close", "export"],
        "development.indicators": ["view", "manage"],
        "development.sensitive_notes": ["view", "create"],
    }
    for module, actions in modules.items():
        for action in actions:
            permission_rows.append({"name": f"{module}.{action}", "module": module, "action": action, "description": f"{action.replace('_',' ').title()} {module.replace('.',' ')}"})
    conn = op.get_bind()
    for row in permission_rows:
        conn.execute(sa.text("INSERT INTO permissions (name,module,action,description) SELECT :name,:module,:action,:description WHERE NOT EXISTS (SELECT 1 FROM permissions WHERE name=:name)"), row)
    conn.execute(sa.text("INSERT INTO roles (name,is_system,permissions_configured) SELECT 'Counselor', true, true WHERE NOT EXISTS (SELECT 1 FROM roles WHERE name='Counselor')"))
    role_id = conn.execute(sa.text("SELECT id FROM roles WHERE name='Counselor'")).scalar()
    for name in ["dashboard.view","children.view","development.view","development.create","development.update","development.submit","development.review","development.close","development.export","development.sensitive_notes.view","development.sensitive_notes.create","development.indicators.view"]:
        permission_id = conn.execute(sa.text("SELECT id FROM permissions WHERE name=:name"), {"name": name}).scalar()
        if role_id and permission_id:
            conn.execute(sa.text("INSERT INTO role_permissions (role_id,permission_id) SELECT :role_id,:permission_id WHERE NOT EXISTS (SELECT 1 FROM role_permissions WHERE role_id=:role_id AND permission_id=:permission_id)"), {"role_id": role_id, "permission_id": permission_id})
    role_defaults = {
        "Manager": ["development.view","development.create","development.update","development.review","development.close","development.export","development.indicators.view","development.sensitive_notes.view","development.sensitive_notes.create"],
        "Data Entry Operator": ["development.view","development.create","development.update","development.submit","development.indicators.view"],
        "Warden": ["development.view","development.create","development.submit"],
        "Viewer": ["development.view"],
    }
    for role_name, names in role_defaults.items():
        existing_role_id = conn.execute(sa.text("SELECT id FROM roles WHERE name=:name"), {"name": role_name}).scalar()
        for permission_name in names:
            permission_id = conn.execute(sa.text("SELECT id FROM permissions WHERE name=:name"), {"name": permission_name}).scalar()
            if existing_role_id and permission_id:
                conn.execute(sa.text("INSERT INTO role_permissions (role_id,permission_id) SELECT :role_id,:permission_id WHERE NOT EXISTS (SELECT 1 FROM role_permissions WHERE role_id=:role_id AND permission_id=:permission_id)"), {"role_id": existing_role_id, "permission_id": permission_id})


def downgrade() -> None:
    op.drop_index("ix_child_development_observation_responses_indicator_id", table_name="child_development_observation_responses")
    op.drop_index("ix_child_development_observation_responses_observation_id", table_name="child_development_observation_responses")
    op.drop_table("child_development_observation_responses")
    op.drop_index("ix_child_development_observations_urgent_flag", table_name="child_development_observations")
    op.drop_index("ix_child_development_observations_review_status", table_name="child_development_observations")
    op.drop_index("ix_child_development_observations_observation_frequency", table_name="child_development_observations")
    op.drop_index("ix_child_development_observations_observation_date", table_name="child_development_observations")
    op.drop_index("ix_child_development_observations_child_id", table_name="child_development_observations")
    op.drop_table("child_development_observations")
    op.drop_index("ix_development_indicators_category", table_name="development_indicators")
    op.drop_index("ix_development_indicators_indicator_code", table_name="development_indicators")
    op.drop_table("development_indicators")
