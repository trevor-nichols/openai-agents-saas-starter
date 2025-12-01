"""add soft delete columns to workflow runs"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "20251201_120000"
down_revision: Union[str, None] = "24af559c0832"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "workflow_runs", sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column("workflow_runs", sa.Column("deleted_by", sa.String(), nullable=True))
    op.add_column("workflow_runs", sa.Column("deleted_reason", sa.String(), nullable=True))
    op.create_index(
        op.f("ix_workflow_runs_deleted_at"), "workflow_runs", ["deleted_at"], unique=False
    )

    op.add_column(
        "workflow_run_steps",
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column("workflow_run_steps", sa.Column("deleted_by", sa.String(), nullable=True))
    op.add_column("workflow_run_steps", sa.Column("deleted_reason", sa.String(), nullable=True))
    op.create_index(
        op.f("ix_workflow_run_steps_deleted_at"),
        "workflow_run_steps",
        ["deleted_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_workflow_run_steps_deleted_at"), table_name="workflow_run_steps")
    op.drop_column("workflow_run_steps", "deleted_reason")
    op.drop_column("workflow_run_steps", "deleted_by")
    op.drop_column("workflow_run_steps", "deleted_at")

    op.drop_index(op.f("ix_workflow_runs_deleted_at"), table_name="workflow_runs")
    op.drop_column("workflow_runs", "deleted_reason")
    op.drop_column("workflow_runs", "deleted_by")
    op.drop_column("workflow_runs", "deleted_at")
