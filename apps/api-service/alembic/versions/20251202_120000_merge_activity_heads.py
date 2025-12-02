"""Merge diverged heads after activity log landing.

Revision ID: 20251202_120000
Revises: 24af559c0832, 20251126_130200, c3c9b1f4cf29
Create Date: 2025-12-02
"""

revision = "20251202_120000"
down_revision = ("24af559c0832", "20251126_130200", "c3c9b1f4cf29")
branch_labels = None
depends_on = None


def upgrade() -> None:
    """No-op merge revision to stitch branches."""
    pass


def downgrade() -> None:
    """No-op merge revision to unwind stitch."""
    pass
