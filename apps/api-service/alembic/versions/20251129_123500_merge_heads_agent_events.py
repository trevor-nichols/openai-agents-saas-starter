"""Merge heads after agent run events."""

from __future__ import annotations

from alembic import op

# revision identifiers, used by Alembic.
revision = "20251129_123500"
down_revision = ("20251129_120000", "2025_11_27_02")
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Merge point; no DDL required.
    pass


def downgrade() -> None:
    # Downgrade would reintroduce split heads; not supported.
    raise RuntimeError("Downgrade through merge head is not supported.")
