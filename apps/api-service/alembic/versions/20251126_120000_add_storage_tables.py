"""Create storage bucket and object tables for multi-provider storage."""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "20251126_120000"
down_revision = ("636feb5dd51a", "4f9a8c7e3b4d")
branch_labels = None
depends_on = None


def _utcnow_default() -> sa.TextClause:
    """Return a cross-dialect 'now' expression compatible with SQLite and Postgres."""

    bind = op.get_bind()
    if bind is not None and bind.dialect.name == "sqlite":
        return sa.text("CURRENT_TIMESTAMP")
    return sa.text("timezone('utc', now())")


def _json_type(bind) -> sa.types.TypeEngine:
    if bind is not None and bind.dialect.name == "sqlite":
        return sa.JSON()
    return postgresql.JSONB(astext_type=sa.Text())


def upgrade() -> None:
    utc_now = _utcnow_default()
    bind = op.get_bind()
    json_type = _json_type(bind)
    empty_json_default = sa.text("'{}'::jsonb") if bind and bind.dialect.name != "sqlite" else sa.text("'{}'")

    op.create_table(
        "storage_buckets",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("provider", sa.String(length=16), nullable=False),
        sa.Column("bucket_name", sa.String(length=128), nullable=False),
        sa.Column("region", sa.String(length=64), nullable=True),
        sa.Column("prefix", sa.String(length=128), nullable=True),
        sa.Column("is_default", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("status", sa.String(length=16), nullable=False, server_default="ready"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=utc_now),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=utc_now),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenant_accounts.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("tenant_id", "bucket_name", name="uq_storage_buckets_tenant_name"),
    )
    op.create_index(
        "ix_storage_buckets_tenant_provider",
        "storage_buckets",
        ["tenant_id", "provider"],
    )

    op.create_table(
        "storage_objects",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("bucket_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("object_key", sa.String(length=512), nullable=False),
        sa.Column("filename", sa.String(length=256), nullable=False),
        sa.Column("mime_type", sa.String(length=128), nullable=True),
        sa.Column("size_bytes", sa.BigInteger(), nullable=True),
        sa.Column("checksum_sha256", sa.String(length=64), nullable=True),
        sa.Column("status", sa.String(length=16), nullable=False, server_default="pending"),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("agent_key", sa.String(length=64), nullable=True),
        sa.Column("conversation_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("metadata_json", json_type, nullable=False, server_default=empty_json_default),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=utc_now),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=utc_now),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenant_accounts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["bucket_id"], ["storage_buckets.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["conversation_id"], ["agent_conversations.id"], ondelete="SET NULL"),
        sa.UniqueConstraint("bucket_id", "object_key", name="uq_storage_objects_bucket_key"),
    )
    op.create_index(
        "ix_storage_objects_tenant_status",
        "storage_objects",
        ["tenant_id", "status"],
    )
    op.create_index(
        "ix_storage_objects_conversation",
        "storage_objects",
        ["conversation_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_storage_objects_conversation", table_name="storage_objects")
    op.drop_index("ix_storage_objects_tenant_status", table_name="storage_objects")
    op.drop_table("storage_objects")
    op.drop_index("ix_storage_buckets_tenant_provider", table_name="storage_buckets")
    op.drop_table("storage_buckets")
