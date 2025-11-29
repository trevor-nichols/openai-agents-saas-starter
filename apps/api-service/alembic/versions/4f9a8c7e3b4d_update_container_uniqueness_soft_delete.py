"""Update container uniqueness to allow reuse after soft delete.

Revision ID: 4f9a8c7e3b4d
Revises: 3e0c5e5a1c2b
Create Date: 2025-11-26 17:10:00.000000
"""

from __future__ import annotations

from alembic import op
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision = "4f9a8c7e3b4d"
down_revision = "3e0c5e5a1c2b"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    if bind and bind.dialect.name == "sqlite":
        # SQLite cannot drop unique constraints easily; skip to avoid destructive table rebuild
        return

    op.drop_constraint("uq_containers_tenant_name", "containers", type_="unique")
    op.create_unique_constraint(
        "uq_containers_tenant_name", "containers", ["tenant_id", "name", "deleted_at"]
    )


def downgrade() -> None:
    bind = op.get_bind()
    if bind and bind.dialect.name == "sqlite":
        return

    op.drop_constraint("uq_containers_tenant_name", "containers", type_="unique")
    op.create_unique_constraint("uq_containers_tenant_name", "containers", ["tenant_id", "name"])
