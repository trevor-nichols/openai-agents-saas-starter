"""Add partial unique index for tenant-level usage counters.

Revision ID: 20251207_120000
Revises: 20251206_160000
Create Date: 2025-12-07 12:00:00
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "20251207_120000"
down_revision = "20251206_160000"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index(
        "uq_usage_counters_tenant_period_null_user",
        "usage_counters",
        ["tenant_id", "period_start", "granularity"],
        unique=True,
        postgresql_where=sa.text("user_id IS NULL"),
        sqlite_where=sa.text("user_id IS NULL"),
    )


def downgrade() -> None:
    op.drop_index(
        "uq_usage_counters_tenant_period_null_user", table_name="usage_counters"
    )
