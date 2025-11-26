"""Add containers and agent container bindings for code interpreter.

Revision ID: 2f2cbe6b9b1d
Revises: 6724700351b6
Create Date: 2025-11-26 15:00:00.000000
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "2f2cbe6b9b1d"
down_revision = "6724700351b6"
branch_labels = None
depends_on = None


def _uuid_type() -> sa.types.TypeEngine:
    dialect = op.get_bind().dialect.name if op.get_bind() else ""
    if dialect == "postgresql":
        from sqlalchemy.dialects.postgresql import UUID

        return UUID(as_uuid=True)
    return sa.String(length=36)


def _utc_now_default():
    dialect = op.get_bind().dialect.name if op.get_bind() else ""
    if dialect == "postgresql":
        return sa.text("timezone('utc', now())")
    return sa.text("CURRENT_TIMESTAMP")


def upgrade() -> None:
    uuid_type = _uuid_type()
    utc_now = _utc_now_default()

    op.create_table(
        "containers",
        sa.Column("id", uuid_type, primary_key=True),
        sa.Column("openai_id", sa.String(length=64), nullable=False, unique=True),
        sa.Column("tenant_id", uuid_type, sa.ForeignKey("tenant_accounts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("owner_user_id", uuid_type, sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("memory_limit", sa.String(length=8), nullable=False, server_default=sa.text("'1g'")),
        sa.Column("status", sa.String(length=32), nullable=False, server_default=sa.text("'running'")),
        sa.Column("expires_after", sa.JSON(), nullable=True),
        sa.Column("last_active_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=utc_now),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=utc_now),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("tenant_id", "name", name="uq_containers_tenant_name"),
    )

    op.create_index("ix_containers_tenant_status", "containers", ["tenant_id", "status"])
    op.create_index("ix_containers_tenant_created", "containers", ["tenant_id", "created_at"])

    op.create_table(
        "agent_containers",
        sa.Column("agent_key", sa.String(length=64), nullable=False),
        sa.Column(
            "container_id",
            uuid_type,
            sa.ForeignKey("containers.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "tenant_id",
            uuid_type,
            sa.ForeignKey("tenant_accounts.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("agent_key", "container_id", "tenant_id"),
    )


def downgrade() -> None:
    op.drop_table("agent_containers")
    op.drop_index("ix_containers_tenant_created", table_name="containers")
    op.drop_index("ix_containers_tenant_status", table_name="containers")
    op.drop_table("containers")
