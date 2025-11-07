"""Add SDK session metadata columns and backing tables."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "6724700351b6"
down_revision = "45c4400e74d9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "agent_conversations",
        sa.Column("sdk_session_id", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "agent_conversations",
        sa.Column("session_cursor", sa.String(length=128), nullable=True),
    )
    op.add_column(
        "agent_conversations",
        sa.Column(
            "last_session_sync_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )

    op.create_table(
        "sdk_agent_sessions",
        sa.Column("session_id", sa.String(length=255), primary_key=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("timezone('utc', now())"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("timezone('utc', now())"),
        ),
    )

    op.create_table(
        "sdk_agent_session_messages",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column(
            "session_id",
            sa.String(length=255),
            sa.ForeignKey(
                "sdk_agent_sessions.session_id",
                ondelete="CASCADE",
            ),
            nullable=False,
        ),
        sa.Column("message_data", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("timezone('utc', now())"),
        ),
        sqlite_autoincrement=True,
    )

    op.create_index(
        "ix_sdk_agent_session_messages_session_time",
        "sdk_agent_session_messages",
        ["session_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_sdk_agent_session_messages_session_time",
        table_name="sdk_agent_session_messages",
    )
    op.drop_table("sdk_agent_session_messages")
    op.drop_table("sdk_agent_sessions")

    op.drop_column("agent_conversations", "last_session_sync_at")
    op.drop_column("agent_conversations", "session_cursor")
    op.drop_column("agent_conversations", "sdk_session_id")
