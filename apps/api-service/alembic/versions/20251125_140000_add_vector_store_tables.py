"""Create vector store and vector store file tables for RAG support."""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "20251125_140000"
down_revision = "20251123_120000"
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
        "vector_stores",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("openai_id", sa.String(length=64), nullable=False, unique=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("owner_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "status",
            sa.String(length=16),
            nullable=False,
            server_default="creating",
        ),
        sa.Column("usage_bytes", sa.BigInteger(), nullable=False, server_default=sa.text("0")),
        sa.Column("expires_after", json_type, nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_active_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("metadata_json", json_type, nullable=False, server_default=empty_json_default),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=utc_now),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=utc_now,
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenant_accounts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["owner_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.UniqueConstraint("tenant_id", "name", name="uq_vector_stores_tenant_name"),
    )

    op.create_index(
        "ix_vector_stores_tenant_status",
        "vector_stores",
        ["tenant_id", "status"],
    )
    op.create_index(
        "ix_vector_stores_tenant_created",
        "vector_stores",
        ["tenant_id", "created_at"],
    )

    op.create_table(
        "vector_store_files",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("openai_file_id", sa.String(length=64), nullable=False),
        sa.Column("vector_store_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("filename", sa.String(length=256), nullable=False),
        sa.Column("mime_type", sa.String(length=128), nullable=True),
        sa.Column("size_bytes", sa.BigInteger(), nullable=True),
        sa.Column("usage_bytes", sa.BigInteger(), nullable=False, server_default=sa.text("0")),
        sa.Column(
            "status",
            sa.String(length=16),
            nullable=False,
            server_default="indexing",
        ),
        sa.Column("attributes_json", json_type, nullable=False, server_default=empty_json_default),
        sa.Column("chunking_json", json_type, nullable=True),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=utc_now),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=utc_now,
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["vector_store_id"],
            ["vector_stores.id"],
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint(
            "vector_store_id",
            "openai_file_id",
            name="uq_vector_store_files_store_file",
        ),
    )

    op.create_index(
        "ix_vector_store_files_store_status",
        "vector_store_files",
        ["vector_store_id", "status"],
    )

    op.create_table(
        "agent_vector_stores",
        sa.Column("agent_key", sa.String(length=64), nullable=False),
        sa.Column("vector_store_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenant_accounts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["vector_store_id"], ["vector_stores.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("agent_key", "vector_store_id", "tenant_id"),
    )


def downgrade() -> None:
    op.drop_table("agent_vector_stores")
    op.drop_index("ix_vector_store_files_store_status", table_name="vector_store_files")
    op.drop_table("vector_store_files")
    op.drop_index("ix_vector_stores_tenant_created", table_name="vector_stores")
    op.drop_index("ix_vector_stores_tenant_status", table_name="vector_stores")
    op.drop_table("vector_stores")
