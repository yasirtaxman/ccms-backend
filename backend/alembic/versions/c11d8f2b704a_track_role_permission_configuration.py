"""Track explicit role permission configuration.

Revision ID: c11d8f2b704a
Revises: b11c4e7a903f
Create Date: 2026-06-22
"""
from alembic import op
import sqlalchemy as sa
revision="c11d8f2b704a";down_revision="b11c4e7a903f";branch_labels=None;depends_on=None
def upgrade():
    op.add_column("roles",sa.Column("permissions_configured",sa.Boolean(),server_default=sa.false(),nullable=False))
    op.execute("UPDATE roles SET permissions_configured = TRUE WHERE name IN ('Manager','Data Entry Operator','Viewer','Warden')")
def downgrade():op.drop_column("roles","permissions_configured")
