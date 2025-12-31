"""Add provisioning status to tenant accounts."""

from __future__ import annotations

from alembic import op

revision = "20251231_130000"
down_revision = "56d5bfd1fee5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "ALTER TYPE tenant_account_status ADD VALUE IF NOT EXISTS 'provisioning'"
    )


def downgrade() -> None:
    op.execute(
        "CREATE TYPE tenant_account_status_new AS ENUM ("
        "'active', 'suspended', 'deprovisioning', 'deprovisioned')"
    )
    op.execute(
        "ALTER TABLE tenant_accounts ALTER COLUMN status "
        "TYPE tenant_account_status_new USING status::text::tenant_account_status_new"
    )
    op.execute("DROP TYPE tenant_account_status")
    op.execute("ALTER TYPE tenant_account_status_new RENAME TO tenant_account_status")
