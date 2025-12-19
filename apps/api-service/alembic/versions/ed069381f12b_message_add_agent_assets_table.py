"""Add agent asset catalog table."""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "ed069381f12b"
down_revision = "20251217_120500"
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
    empty_json_default = (
        sa.text("'{}'::jsonb") if bind and bind.dialect.name != "sqlite" else sa.text("'{}'")
    )

    op.create_table(
        "agent_assets",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("storage_object_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("asset_type", sa.String(length=16), nullable=False),
        sa.Column("source_tool", sa.String(length=32), nullable=True),
        sa.Column("conversation_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("message_id", sa.Integer(), nullable=True),
        sa.Column("tool_call_id", sa.String(length=255), nullable=True),
        sa.Column("response_id", sa.String(length=128), nullable=True),
        sa.Column("container_id", sa.String(length=128), nullable=True),
        sa.Column("openai_file_id", sa.String(length=128), nullable=True),
        sa.Column("metadata_json", json_type, nullable=False, server_default=empty_json_default),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=utc_now),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=utc_now),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenant_accounts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["storage_object_id"], ["storage_objects.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["conversation_id"], ["agent_conversations.id"], ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(["message_id"], ["agent_messages.id"], ondelete="SET NULL"),
        sa.UniqueConstraint("storage_object_id", name="uq_agent_assets_storage_object"),
    )
    op.create_index(
        "ix_agent_assets_tenant_type_created",
        "agent_assets",
        ["tenant_id", "asset_type", "created_at"],
    )
    op.create_index(
        "ix_agent_assets_conversation",
        "agent_assets",
        ["conversation_id"],
    )
    op.create_index(
        "ix_agent_assets_message",
        "agent_assets",
        ["message_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_agent_assets_message", table_name="agent_assets")
    op.drop_index("ix_agent_assets_conversation", table_name="agent_assets")
    op.drop_index("ix_agent_assets_tenant_type_created", table_name="agent_assets")
    op.drop_table("agent_assets")
