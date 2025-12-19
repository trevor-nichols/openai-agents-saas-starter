"""Add message/segment linkage for per-message deletion.

Revision ID: 20251217_120500
Revises: 45b781fda5df
Create Date: 2025-12-17
"""

from __future__ import annotations

import uuid

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "20251217_120500"
down_revision = "45b781fda5df"
branch_labels = None
depends_on = None


def _utcnow_default() -> sa.TextClause:
    """Return a cross-dialect 'now' expression compatible with SQLite and Postgres."""

    bind = op.get_bind()
    if bind is not None and bind.dialect.name == "sqlite":
        return sa.text("CURRENT_TIMESTAMP")
    return sa.text("timezone('utc', now())")


def upgrade() -> None:
    utc_now = _utcnow_default()
    uuid_type = postgresql.UUID(as_uuid=True)

    op.add_column(
        "conversation_ledger_segments",
        sa.Column("visible_through_message_position", sa.Integer(), nullable=True),
    )

    # Link persisted app messages to ledger segments so segment truncation hides deleted content.
    op.add_column("agent_messages", sa.Column("segment_id", uuid_type, nullable=True))

    bind = op.get_bind()
    if bind is None:  # pragma: no cover - alembic always provides a bind
        raise RuntimeError("Missing alembic bind")

    # Best-effort backfill: assign existing messages to an active segment per conversation.
    conversations = bind.execute(
        sa.text(
            "SELECT id, tenant_id, created_at, updated_at FROM agent_conversations"
        )
    ).fetchall()

    for conversation_id, tenant_id, created_at, updated_at in conversations:
        active = bind.execute(
            sa.text(
                "SELECT id FROM conversation_ledger_segments "
                "WHERE conversation_id = :cid AND truncated_at IS NULL "
                "ORDER BY segment_index DESC LIMIT 1"
            ),
            {"cid": conversation_id},
        ).fetchone()

        if active:
            segment_id = active[0]
        else:
            latest = bind.execute(
                sa.text(
                    "SELECT segment_index, id FROM conversation_ledger_segments "
                    "WHERE conversation_id = :cid "
                    "ORDER BY segment_index DESC LIMIT 1"
                ),
                {"cid": conversation_id},
            ).fetchone()

            next_index = int(latest[0]) + 1 if latest else 0
            segment_id = uuid.uuid4()
            parent_segment_id = latest[1] if latest else None

            bind.execute(
                sa.text(
                    "INSERT INTO conversation_ledger_segments "
                    "(id, tenant_id, conversation_id, segment_index, parent_segment_id, "
                    " visible_through_event_id, visible_through_message_position, truncated_at, "
                    " created_at, updated_at) "
                    "VALUES "
                    "(:id, :tenant_id, :conversation_id, :segment_index, :parent_segment_id, "
                    " NULL, NULL, NULL, :created_at, :updated_at)"
                ),
                {
                    "id": segment_id,
                    "tenant_id": tenant_id,
                    "conversation_id": conversation_id,
                    "segment_index": next_index,
                    "parent_segment_id": parent_segment_id,
                    "created_at": created_at or bind.execute(sa.select(utc_now)).scalar(),
                    "updated_at": updated_at or bind.execute(sa.select(utc_now)).scalar(),
                },
            )

        bind.execute(
            sa.text(
                "UPDATE agent_messages SET segment_id = :segment_id "
                "WHERE conversation_id = :conversation_id AND segment_id IS NULL"
            ),
            {"segment_id": segment_id, "conversation_id": conversation_id},
        )

    # Enforce non-null + FK once backfill is done.
    op.alter_column("agent_messages", "segment_id", nullable=False)
    op.create_foreign_key(
        "fk_agent_messages_segment_id_conversation_ledger_segments",
        "agent_messages",
        "conversation_ledger_segments",
        ["segment_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_index("ix_agent_messages_segment_id", "agent_messages", ["segment_id"])


def downgrade() -> None:
    op.drop_index("ix_agent_messages_segment_id", table_name="agent_messages")
    op.drop_constraint(
        "fk_agent_messages_segment_id_conversation_ledger_segments",
        "agent_messages",
        type_="foreignkey",
    )
    op.drop_column("agent_messages", "segment_id")
    op.drop_column("conversation_ledger_segments", "visible_through_message_position")

