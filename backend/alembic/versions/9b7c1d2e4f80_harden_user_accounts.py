"""Harden user accounts for production administration.

Revision ID: 9b7c1d2e4f80
Revises: f6a04c9e3b72
Create Date: 2026-06-21
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "9b7c1d2e4f80"
down_revision: Union[str, Sequence[str], None] = "f6a04c9e3b72"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.alter_column("users","full_name",existing_type=sa.String(255),nullable=True)
    op.alter_column("users","email",existing_type=sa.String(255),nullable=True)
    op.add_column("users",sa.Column("force_password_change",sa.Boolean(),server_default=sa.false(),nullable=False))
    op.add_column("users",sa.Column("last_login_at",sa.DateTime(timezone=True),nullable=True))
    op.add_column("users",sa.Column("updated_at",sa.DateTime(timezone=True),server_default=sa.text("CURRENT_TIMESTAMP"),nullable=False))

def downgrade() -> None:
    op.drop_column("users","updated_at"); op.drop_column("users","last_login_at"); op.drop_column("users","force_password_change")
    op.alter_column("users","email",existing_type=sa.String(255),nullable=False)
    op.alter_column("users","full_name",existing_type=sa.String(255),nullable=False)
