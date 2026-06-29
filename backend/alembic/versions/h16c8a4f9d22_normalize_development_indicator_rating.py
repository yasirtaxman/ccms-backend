"""normalize development indicator rating input type

Revision ID: h16c8a4f9d22
Revises: g15b7d9e3f21
Create Date: 2026-06-29 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "h16c8a4f9d22"
down_revision: str | None = "g15b7d9e3f21"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        sa.text(
            "UPDATE development_indicators "
            "SET input_type = 'rating_1_to_5' "
            "WHERE input_type = 'rating'"
        )
    )


def downgrade() -> None:
    op.execute(
        sa.text(
            "UPDATE development_indicators "
            "SET input_type = 'rating' "
            "WHERE input_type = 'rating_1_to_5'"
        )
    )
