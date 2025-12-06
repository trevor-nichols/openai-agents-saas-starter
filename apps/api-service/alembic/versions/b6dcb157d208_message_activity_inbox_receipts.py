"""Add activity inbox receipts and checkpoints"""

revision = 'b6dcb157d208'
down_revision = '6724700351b6'
branch_labels = None
# Ensure activity_events exists before we add receipts/checkpoints that FK it.
depends_on = ('c3c9b1f4cf29',)

from alembic import op  # noqa: E402
import sqlalchemy as sa  # noqa: E402


def upgrade() -> None:
    op.create_table(
        "activity_event_receipts",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("event_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenant_accounts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["event_id"], ["activity_events.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("tenant_id", "user_id", "event_id", name="uq_activity_receipt"),
    )
    op.create_index(
        "ix_activity_receipts_user_status",
        "activity_event_receipts",
        ["tenant_id", "user_id", "status"],
    )

    op.create_table(
        "activity_last_seen",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("last_seen_created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("last_seen_event_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenant_accounts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("tenant_id", "user_id", name="uq_activity_last_seen_user"),
    )
    op.create_index(
        "ix_activity_last_seen_user",
        "activity_last_seen",
        ["tenant_id", "user_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_activity_last_seen_user", table_name="activity_last_seen")
    op.drop_table("activity_last_seen")
    op.drop_index("ix_activity_receipts_user_status", table_name="activity_event_receipts")
    op.drop_table("activity_event_receipts")
