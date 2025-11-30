"""link workflow run events"""

revision = '24af559c0832'
down_revision = '20251129_123500'
branch_labels = None
depends_on = None

from alembic import op  # noqa: E402
import sqlalchemy as sa  # noqa: E402


def upgrade() -> None:
    op.add_column(
        "agent_run_events",
        sa.Column("workflow_run_id", sa.String(length=64), nullable=True),
    )
    op.create_index(
        "ix_agent_run_events_workflow_run",
        "agent_run_events",
        ["workflow_run_id"],
    )
    op.create_index(
        "ix_agent_run_events_workflow_run_seq",
        "agent_run_events",
        ["workflow_run_id", "sequence_no"],
    )
    op.create_foreign_key(
        "fk_agent_run_events_workflow_run",
        "agent_run_events",
        "workflow_runs",
        ["workflow_run_id"],
        ["id"],
        ondelete="SET NULL",
    )

    # Backfill: clear orphaned conversation references so the FK can be applied safely.
    op.execute(
        """
        UPDATE workflow_runs wr
        SET conversation_id = NULL
        WHERE conversation_id IS NOT NULL
          AND NOT EXISTS (
            SELECT 1 FROM agent_conversations ac
            WHERE ac.conversation_key = wr.conversation_id
          );
        """
    )

    op.create_foreign_key(
        "fk_workflow_runs_conversation_key",
        "workflow_runs",
        "agent_conversations",
        ["conversation_id"],
        ["conversation_key"],
        ondelete="SET NULL",
    )
    op.create_index(
        "ix_workflow_runs_conversation_id",
        "workflow_runs",
        ["conversation_id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_workflow_runs_conversation_key",
        "workflow_runs",
        type_="foreignkey",
    )
    op.drop_index("ix_workflow_runs_conversation_id", table_name="workflow_runs")
    op.drop_constraint(
        "fk_agent_run_events_workflow_run",
        "agent_run_events",
        type_="foreignkey",
    )
    op.drop_index("ix_agent_run_events_workflow_run_seq", table_name="agent_run_events")
    op.drop_index("ix_agent_run_events_workflow_run", table_name="agent_run_events")
    op.drop_column("agent_run_events", "workflow_run_id")
