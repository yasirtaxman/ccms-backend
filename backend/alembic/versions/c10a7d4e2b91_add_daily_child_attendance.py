"""Add daily child attendance register.

Revision ID: c10a7d4e2b91
Revises: 9b7c1d2e4f80
Create Date: 2026-06-21
"""
from alembic import op
import sqlalchemy as sa
revision="c10a7d4e2b91"; down_revision="9b7c1d2e4f80"; branch_labels=None; depends_on=None
def upgrade():
    op.create_table("daily_child_attendance",sa.Column("id",sa.Integer(),primary_key=True),sa.Column("organization_id",sa.Integer(),nullable=True),sa.Column("child_id",sa.Integer(),sa.ForeignKey("children.id",ondelete="CASCADE"),nullable=False),sa.Column("attendance_date",sa.Date(),nullable=False),sa.Column("status",sa.String(40),nullable=False),sa.Column("check_in_time",sa.Time(),nullable=True),sa.Column("check_out_time",sa.Time(),nullable=True),sa.Column("marked_by",sa.Integer(),sa.ForeignKey("users.id"),nullable=False),sa.Column("remarks",sa.Text(),nullable=True),sa.Column("created_by",sa.Integer(),sa.ForeignKey("users.id"),nullable=False),sa.Column("updated_by",sa.Integer(),sa.ForeignKey("users.id"),nullable=False),sa.Column("created_at",sa.DateTime(timezone=True),server_default=sa.text("CURRENT_TIMESTAMP"),nullable=False),sa.Column("updated_at",sa.DateTime(timezone=True),server_default=sa.text("CURRENT_TIMESTAMP"),nullable=False),sa.Column("deleted_at",sa.DateTime(timezone=True),nullable=True),sa.Column("deleted_by",sa.Integer(),sa.ForeignKey("users.id"),nullable=True),sa.CheckConstraint("status IN ('Present','Absent','On Leave','Medical Leave','Home Visit','School Activity','Outside Activity','Unauthorized Absence','Missing')",name="ck_daily_child_attendance_status"))
    for column in ("child_id","attendance_date","status","organization_id"): op.create_index(f"ix_daily_child_attendance_{column}","daily_child_attendance",[column])
    op.create_index("uq_daily_child_attendance_active_child_date","daily_child_attendance",["child_id","attendance_date"],unique=True,postgresql_where=sa.text("deleted_at IS NULL"))
def downgrade(): op.drop_table("daily_child_attendance")
