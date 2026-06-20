"""Add case management profiles, notes, counseling, incidents, care plans, and reviews.

Revision ID: f6a04c9e3b72
Revises: e5f93b8d2a61
Create Date: 2026-06-21
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f6a04c9e3b72"
down_revision: Union[str, Sequence[str], None] = "e5f93b8d2a61"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def operational_columns() -> list[sa.Column]:
    return [
        sa.Column("organization_id", sa.Integer(), nullable=True),
        sa.Column("created_by", sa.Integer(), nullable=False),
        sa.Column("updated_by", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_by", sa.Integer(), nullable=True),
    ]


def operational_fks() -> list[sa.ForeignKeyConstraint]:
    return [
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["updated_by"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["deleted_by"], ["users.id"], ondelete="RESTRICT"),
    ]


def operational_indexes(table: str) -> None:
    op.create_index(f"ix_{table}_organization_id", table, ["organization_id"])
    op.create_index(f"ix_{table}_deleted_at", table, ["deleted_at"])


def upgrade() -> None:
    op.create_table(
        "child_case_profiles",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("child_id", sa.Integer(), nullable=False),
        sa.Column("case_number", sa.String(50), nullable=False),
        sa.Column("case_opened_date", sa.Date(), nullable=False),
        sa.Column("case_status", sa.String(20), nullable=False),
        sa.Column("risk_level", sa.String(10), nullable=False),
        sa.Column("welfare_status", sa.String(20), nullable=False),
        sa.Column("assigned_case_worker", sa.String(255), nullable=True),
        sa.Column("case_summary", sa.Text(), nullable=True),
        sa.Column("family_background", sa.Text(), nullable=True),
        sa.Column("psychosocial_summary", sa.Text(), nullable=True),
        sa.Column("current_concerns", sa.Text(), nullable=True),
        sa.Column("care_plan_summary", sa.Text(), nullable=True),
        *operational_columns(),
        sa.CheckConstraint("case_status IN ('Open', 'Under Review', 'Closed', 'Transferred')", name="ck_case_profiles_status"),
        sa.CheckConstraint("risk_level IN ('Low', 'Medium', 'High', 'Critical')", name="ck_case_profiles_risk"),
        sa.CheckConstraint("welfare_status IN ('Stable', 'Needs Attention', 'At Risk', 'Critical')", name="ck_case_profiles_welfare"),
        sa.ForeignKeyConstraint(["child_id"], ["children.id"], ondelete="RESTRICT"),
        sa.UniqueConstraint("child_id", name="uq_child_case_profiles_child_id"),
        sa.UniqueConstraint("case_number", name="uq_child_case_profiles_case_number"),
        *operational_fks(),
    )
    op.create_index("ix_child_case_profiles_child_id", "child_case_profiles", ["child_id"])
    op.create_index("ix_child_case_profiles_case_number", "child_case_profiles", ["case_number"])
    op.create_index("ix_child_case_profiles_case_status", "child_case_profiles", ["case_status"])
    op.create_index("ix_child_case_profiles_risk_level", "child_case_profiles", ["risk_level"])
    op.create_index("ix_child_case_profiles_welfare_status", "child_case_profiles", ["welfare_status"])
    op.create_index("ix_case_profiles_status_risk", "child_case_profiles", ["case_status", "risk_level"])
    operational_indexes("child_case_profiles")

    op.create_table(
        "case_notes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("child_id", sa.Integer(), nullable=False),
        sa.Column("case_profile_id", sa.Integer(), nullable=True),
        sa.Column("note_date", sa.Date(), nullable=False),
        sa.Column("note_type", sa.String(30), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("visibility", sa.String(15), nullable=False),
        sa.Column("follow_up_required", sa.Boolean(), nullable=False),
        sa.Column("follow_up_date", sa.Date(), nullable=True),
        *operational_columns(),
        sa.CheckConstraint("note_type IN ('General', 'Home Visit', 'Family Contact', 'School Contact', 'Medical Follow-up', 'Counseling', 'Behavior', 'Legal', 'Emergency')", name="ck_case_notes_type"),
        sa.CheckConstraint("visibility IN ('Normal', 'Confidential', 'Restricted')", name="ck_case_notes_visibility"),
        sa.CheckConstraint("follow_up_date IS NULL OR follow_up_date >= note_date", name="ck_case_notes_follow_up_date"),
        sa.ForeignKeyConstraint(["child_id"], ["children.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["case_profile_id"], ["child_case_profiles.id"], ondelete="RESTRICT"),
        *operational_fks(),
    )
    for name in ("child_id", "case_profile_id", "note_date", "note_type", "visibility", "follow_up_required", "follow_up_date"):
        op.create_index(f"ix_case_notes_{name}", "case_notes", [name])
    op.create_index("ix_case_notes_child_date", "case_notes", ["child_id", "note_date"])
    op.create_index("ix_case_notes_follow_up", "case_notes", ["follow_up_required", "follow_up_date"])
    operational_indexes("case_notes")

    op.create_table(
        "counseling_sessions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("child_id", sa.Integer(), nullable=False),
        sa.Column("session_date", sa.Date(), nullable=False),
        sa.Column("counselor_name", sa.String(255), nullable=False),
        sa.Column("session_type", sa.String(15), nullable=False),
        sa.Column("session_summary", sa.Text(), nullable=True),
        sa.Column("observations", sa.Text(), nullable=True),
        sa.Column("recommendations", sa.Text(), nullable=True),
        sa.Column("next_session_date", sa.Date(), nullable=True),
        sa.Column("status", sa.String(15), nullable=False),
        *operational_columns(),
        sa.CheckConstraint("session_type IN ('Individual', 'Group', 'Family', 'Emergency')", name="ck_counseling_sessions_type"),
        sa.CheckConstraint("status IN ('Completed', 'Scheduled', 'Cancelled')", name="ck_counseling_sessions_status"),
        sa.CheckConstraint("next_session_date IS NULL OR next_session_date >= session_date", name="ck_counseling_sessions_next_date"),
        sa.ForeignKeyConstraint(["child_id"], ["children.id"], ondelete="RESTRICT"),
        *operational_fks(),
    )
    for name in ("child_id", "session_date", "next_session_date", "status"):
        op.create_index(f"ix_counseling_sessions_{name}", "counseling_sessions", [name])
    operational_indexes("counseling_sessions")

    op.create_table(
        "incident_records",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("child_id", sa.Integer(), nullable=False),
        sa.Column("incident_date", sa.Date(), nullable=False),
        sa.Column("incident_type", sa.String(20), nullable=False),
        sa.Column("severity", sa.String(10), nullable=False),
        sa.Column("location", sa.String(255), nullable=True),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("immediate_action_taken", sa.Text(), nullable=True),
        sa.Column("reported_by", sa.String(255), nullable=False),
        sa.Column("review_status", sa.String(20), nullable=False),
        sa.Column("reviewed_by", sa.Integer(), nullable=True),
        sa.Column("reviewed_at", sa.Date(), nullable=True),
        *operational_columns(),
        sa.CheckConstraint("incident_type IN ('Behavioral', 'Safety', 'Health', 'Discipline', 'Protection', 'Missing', 'Conflict', 'Other')", name="ck_incidents_type"),
        sa.CheckConstraint("severity IN ('Low', 'Medium', 'High', 'Critical')", name="ck_incidents_severity"),
        sa.CheckConstraint("review_status IN ('Pending Review', 'Reviewed', 'Closed')", name="ck_incidents_review_status"),
        sa.CheckConstraint("reviewed_at IS NULL OR reviewed_at >= incident_date", name="ck_incidents_reviewed_at"),
        sa.ForeignKeyConstraint(["child_id"], ["children.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["reviewed_by"], ["users.id"], ondelete="RESTRICT"),
        *operational_fks(),
    )
    for name in ("child_id", "incident_date", "incident_type", "severity", "review_status"):
        op.create_index(f"ix_incident_records_{name}", "incident_records", [name])
    op.create_index("ix_incidents_child_date", "incident_records", ["child_id", "incident_date"])
    operational_indexes("incident_records")

    op.create_table(
        "care_plans",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("child_id", sa.Integer(), nullable=False),
        sa.Column("case_profile_id", sa.Integer(), nullable=True),
        sa.Column("plan_title", sa.String(255), nullable=False),
        sa.Column("plan_start_date", sa.Date(), nullable=False),
        sa.Column("plan_end_date", sa.Date(), nullable=True),
        sa.Column("goal_area", sa.String(30), nullable=False),
        sa.Column("goals", sa.Text(), nullable=False),
        sa.Column("planned_actions", sa.Text(), nullable=True),
        sa.Column("responsible_person", sa.String(255), nullable=True),
        sa.Column("status", sa.String(15), nullable=False),
        sa.Column("progress_notes", sa.Text(), nullable=True),
        *operational_columns(),
        sa.CheckConstraint("goal_area IN ('Education', 'Health', 'Behavior', 'Emotional Support', 'Family Reunification', 'Legal', 'Life Skills', 'General Welfare')", name="ck_care_plans_goal_area"),
        sa.CheckConstraint("status IN ('Active', 'Completed', 'On Hold', 'Cancelled')", name="ck_care_plans_status"),
        sa.CheckConstraint("plan_end_date IS NULL OR plan_end_date >= plan_start_date", name="ck_care_plans_dates"),
        sa.ForeignKeyConstraint(["child_id"], ["children.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["case_profile_id"], ["child_case_profiles.id"], ondelete="RESTRICT"),
        *operational_fks(),
    )
    for name in ("child_id", "case_profile_id", "goal_area", "status", "plan_start_date"):
        op.create_index(f"ix_care_plans_{name}", "care_plans", [name])
    op.create_index("ix_care_plans_child_status", "care_plans", ["child_id", "status"])
    op.create_index("uq_care_plans_active_goal", "care_plans", ["child_id", "goal_area"], unique=True, postgresql_where=sa.text("status = 'Active' AND deleted_at IS NULL"))
    operational_indexes("care_plans")

    op.create_table(
        "case_reviews",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("child_id", sa.Integer(), nullable=False),
        sa.Column("case_profile_id", sa.Integer(), nullable=True),
        sa.Column("review_date", sa.Date(), nullable=False),
        sa.Column("review_type", sa.String(15), nullable=False),
        sa.Column("participants", sa.Text(), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("decisions", sa.Text(), nullable=True),
        sa.Column("next_review_date", sa.Date(), nullable=True),
        sa.Column("status", sa.String(15), nullable=False),
        *operational_columns(),
        sa.CheckConstraint("review_type IN ('Monthly', 'Quarterly', 'Annual', 'Special', 'Emergency')", name="ck_case_reviews_type"),
        sa.CheckConstraint("status IN ('Completed', 'Pending', 'Cancelled')", name="ck_case_reviews_status"),
        sa.CheckConstraint("next_review_date IS NULL OR next_review_date >= review_date", name="ck_case_reviews_next_date"),
        sa.ForeignKeyConstraint(["child_id"], ["children.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["case_profile_id"], ["child_case_profiles.id"], ondelete="RESTRICT"),
        *operational_fks(),
    )
    for name in ("child_id", "case_profile_id", "review_date", "next_review_date", "status"):
        op.create_index(f"ix_case_reviews_{name}", "case_reviews", [name])
    op.create_index("ix_case_reviews_child_date", "case_reviews", ["child_id", "review_date"])
    operational_indexes("case_reviews")


def downgrade() -> None:
    op.drop_table("case_reviews")
    op.drop_table("care_plans")
    op.drop_table("incident_records")
    op.drop_table("counseling_sessions")
    op.drop_table("case_notes")
    op.drop_table("child_case_profiles")
