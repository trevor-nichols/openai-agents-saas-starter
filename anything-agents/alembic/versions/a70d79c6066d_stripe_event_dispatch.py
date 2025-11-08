"""Add stripe event dispatch table"""

from alembic import op  # noqa: E402
import sqlalchemy as sa  # noqa: E402
from sqlalchemy.dialects import postgresql  # noqa: E402


revision = "a70d79c6066d"
down_revision = "636feb5dd51a"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "stripe_event_dispatch",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "stripe_event_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("stripe_events.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("handler", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="pending"),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_attempt_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("next_retry_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("timezone('utc', now())"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("timezone('utc', now())"), nullable=False),
        sa.UniqueConstraint("stripe_event_id", "handler", name="uq_stripe_event_dispatch_handler"),
    )
    op.create_index(
        "ix_stripe_event_dispatch_handler_status",
        "stripe_event_dispatch",
        ["handler", "status", "next_retry_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_stripe_event_dispatch_handler_status", table_name="stripe_event_dispatch")
    op.drop_table("stripe_event_dispatch")
