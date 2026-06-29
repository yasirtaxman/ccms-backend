"""fix invalid demo school email

Revision ID: j18e0c6d4b52
Revises: i17d9b5c3a41
Create Date: 2026-06-29 00:20:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "j18e0c6d4b52"
down_revision: str | None = "i17d9b5c3a41"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        sa.text(
            "UPDATE schools "
            "SET email = 'demo.school@ccms.org' "
            "WHERE lower(email) = 'school@demo.ccms.local'"
        )
    )
    op.execute(
        sa.text(
            "UPDATE schools "
            "SET email = NULL "
            "WHERE email IS NOT NULL AND lower(email) LIKE '%.local'"
        )
    )


def downgrade() -> None:
    op.execute(
        sa.text(
            "UPDATE schools "
            "SET email = 'school@demo.ccms.local' "
            "WHERE school_code = 'DEMO-SCH-001' AND email = 'demo.school@ccms.org'"
        )
    )
