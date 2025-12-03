"""Merge workflow soft-delete and activity heads.

Revision ID: 20251203_120000
Revises: 20251201_120000, 20251202_120000
Create Date: 2025-12-03 00:00:00
"""

from alembic import op  # noqa: F401

# revision identifiers, used by Alembic.
revision = "20251203_120000"
down_revision = ("20251201_120000", "20251202_120000")
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Merge revision; no-op upgrade.
    pass


def downgrade() -> None:
    # Merge revision; no-op downgrade.
    pass

