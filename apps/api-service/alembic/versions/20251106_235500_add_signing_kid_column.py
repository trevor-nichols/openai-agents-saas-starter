"""Add signing_kid column for refresh tokens."""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "20251106_235500"
down_revision = "20251106_230500"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    dialect = bind.dialect.name if bind is not None else ""

    op.add_column(
        "service_account_tokens",
        sa.Column(
            "signing_kid",
            sa.String(length=64),
            nullable=False,
            server_default="ed25519-active",
        ),
    )
    if dialect != "sqlite":
        op.alter_column("service_account_tokens", "signing_kid", server_default=None)


def downgrade() -> None:
    op.drop_column("service_account_tokens", "signing_kid")
