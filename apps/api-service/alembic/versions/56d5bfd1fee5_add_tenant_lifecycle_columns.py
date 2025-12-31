"""Add tenant lifecycle columns."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "56d5bfd1fee5"
down_revision = "a3634d48cb21"
branch_labels = None
depends_on = None


def upgrade() -> None:
    status_enum = postgresql.ENUM(
        "active",
        "suspended",
        "deprovisioning",
        "deprovisioned",
        name="tenant_account_status",
        create_type=False,
    )
    status_enum.create(op.get_bind(), checkfirst=True)

    op.add_column(
        "tenant_accounts",
        sa.Column(
            "status",
            status_enum,
            nullable=False,
            server_default="active",
        ),
    )
    op.add_column(
        "tenant_accounts",
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("timezone('utc', now())"),
        ),
    )
    op.add_column(
        "tenant_accounts",
        sa.Column("status_updated_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "tenant_accounts",
        sa.Column("status_updated_by", sa.UUID(), nullable=True),
    )
    op.add_column(
        "tenant_accounts",
        sa.Column("status_reason", sa.String(length=256), nullable=True),
    )
    op.add_column(
        "tenant_accounts",
        sa.Column("suspended_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "tenant_accounts",
        sa.Column("deprovisioned_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_tenant_accounts_status",
        "tenant_accounts",
        ["status"],
        unique=False,
    )
    op.create_foreign_key(
        op.f("fk_tenant_accounts_status_updated_by_users"),
        "tenant_accounts",
        "users",
        ["status_updated_by"],
        ["id"],
        ondelete="SET NULL",
    )

    op.alter_column("tenant_accounts", "status", server_default=None)
    op.alter_column("tenant_accounts", "updated_at", server_default=None)


def downgrade() -> None:
    status_enum = postgresql.ENUM(
        "active",
        "suspended",
        "deprovisioning",
        "deprovisioned",
        name="tenant_account_status",
        create_type=False,
    )

    op.drop_constraint(
        op.f("fk_tenant_accounts_status_updated_by_users"),
        "tenant_accounts",
        type_="foreignkey",
    )
    op.drop_index("ix_tenant_accounts_status", table_name="tenant_accounts")
    op.drop_column("tenant_accounts", "deprovisioned_at")
    op.drop_column("tenant_accounts", "suspended_at")
    op.drop_column("tenant_accounts", "status_reason")
    op.drop_column("tenant_accounts", "status_updated_by")
    op.drop_column("tenant_accounts", "status_updated_at")
    op.drop_column("tenant_accounts", "updated_at")
    op.drop_column("tenant_accounts", "status")

    status_enum.drop(op.get_bind(), checkfirst=True)
