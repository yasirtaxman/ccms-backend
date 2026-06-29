"""fix invalid demo sponsor email

Revision ID: i17d9b5c3a41
Revises: h16c8a4f9d22
Create Date: 2026-06-29 00:10:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "i17d9b5c3a41"
down_revision: str | None = "h16c8a4f9d22"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        sa.text(
            "UPDATE sponsors "
            "SET email = 'demo.sponsor@ccms.org' "
            "WHERE lower(email) = 'sponsor@demo.ccms.local'"
        )
    )
    op.execute(
        sa.text(
            "UPDATE sponsors "
            "SET email = NULL "
            "WHERE email IS NOT NULL AND lower(email) LIKE '%.local'"
        )
    )


def downgrade() -> None:
    op.execute(
        sa.text(
            "UPDATE sponsors "
            "SET email = 'sponsor@demo.ccms.local' "
            "WHERE sponsor_code = 'DEMO-SP-001' AND email = 'demo.sponsor@ccms.org'"
        )
    )
