"""Add email verification tracking to users"""
# isort:skip_file
from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "bcb7e73b5f7b"
down_revision = "a70d79c6066d"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("email_verified_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.execute(
        "UPDATE users SET email_verified_at = timezone('utc', now()) "
        "WHERE email_verified_at IS NULL"
    )


def downgrade() -> None:
    op.drop_column("users", "email_verified_at")
