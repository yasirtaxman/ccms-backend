"""fix invalid demo user emails

Revision ID: k19f1d7e5c63
Revises: j18e0c6d4b52
Create Date: 2026-06-29 00:30:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "k19f1d7e5c63"
down_revision: str | None = "j18e0c6d4b52"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


DEMO_EMAILS = {
    "demo_admin": "admin@example.com",
    "demo_manager": "manager@example.com",
    "demo_warden": "warden@example.com",
    "demo_viewer": "viewer@example.com",
}


def upgrade() -> None:
    for username, email in DEMO_EMAILS.items():
        op.execute(
            sa.text("UPDATE users SET email = :email WHERE username = :username").bindparams(
                email=email,
                username=username,
            )
        )
    op.execute(
        sa.text(
            "UPDATE users "
            "SET email = NULL "
            "WHERE email IS NOT NULL AND lower(email) LIKE '%.local'"
        )
    )


def downgrade() -> None:
    for username in DEMO_EMAILS:
        op.execute(
            sa.text(
                "UPDATE users "
                "SET email = :email "
                "WHERE username = :username"
            ).bindparams(
                email=f"{username}@demo.ccms.local",
                username=username,
            )
        )
