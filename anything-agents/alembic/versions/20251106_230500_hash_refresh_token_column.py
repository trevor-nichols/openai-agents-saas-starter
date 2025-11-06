"""Rename refresh_token column to refresh_token_hash and purge plaintext values."""

from __future__ import annotations

from alembic import op

# revision identifiers, used by Alembic.
revision = "20251106_230500"
down_revision = "20251106_220000"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "service_account_tokens",
        "refresh_token",
        new_column_name="refresh_token_hash",
    )
    op.execute("TRUNCATE TABLE service_account_tokens")


def downgrade() -> None:
    op.alter_column(
        "service_account_tokens",
        "refresh_token_hash",
        new_column_name="refresh_token",
    )
