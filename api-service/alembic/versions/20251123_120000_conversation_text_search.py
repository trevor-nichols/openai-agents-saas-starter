"""Add full-text search support for agent messages and pagination indexes."""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "20251123_120000"
down_revision = ("dfe6a471e8c0", "636feb5dd51a")
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    dialect = bind.dialect.name if bind is not None else ""

    # Full-text search column.
    if dialect == "postgresql":  # pragma: no cover - migration logic
        op.add_column(
            "agent_messages",
            sa.Column(
                "text_tsv",
                postgresql.TSVECTOR(),
                sa.Computed(
                    "to_tsvector('english', coalesce(content->>'text', ''))",
                    persisted=True,
                ),
                nullable=False,
            ),
        )
        op.create_index(
            "ix_agent_messages_text_tsv",
            "agent_messages",
            ["text_tsv"],
            postgresql_using="gin",
        )
    else:
        # SQLite/dev: add a simple text column so ORM queries work; computed expression
        # is stripped by ORM compiles.
        op.add_column("agent_messages", sa.Column("text_tsv", sa.Text(), nullable=True))

    # Helpful composite index for filtered conversation listings.
    op.create_index(
        "ix_agent_conversations_tenant_agent_updated",
        "agent_conversations",
        ["tenant_id", "agent_entrypoint", "updated_at"],
    )


def downgrade() -> None:
    bind = op.get_bind()
    dialect = bind.dialect.name if bind is not None else ""

    op.drop_index(
        "ix_agent_conversations_tenant_agent_updated",
        table_name="agent_conversations",
    )

    if dialect == "postgresql":  # pragma: no cover - migration logic
        op.drop_index(
            "ix_agent_messages_text_tsv",
            table_name="agent_messages",
        )
    op.drop_column("agent_messages", "text_tsv")
