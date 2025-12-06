"""Add composite indexes for workflow run listing."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "20251128_090000"
down_revision = "dfe6a471e8c0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index(
        "ix_workflow_runs_tenant_workflow_started_desc",
        "workflow_runs",
        [sa.column("tenant_id"), sa.column("workflow_key"), sa.column("started_at").desc()],
    )
    op.create_index(
        "ix_workflow_runs_tenant_status_started_desc",
        "workflow_runs",
        [sa.column("tenant_id"), sa.column("status"), sa.column("started_at").desc()],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_workflow_runs_tenant_status_started_desc",
        table_name="workflow_runs",
    )
    op.drop_index(
        "ix_workflow_runs_tenant_workflow_started_desc",
        table_name="workflow_runs",
    )
