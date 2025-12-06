"""add parallel metadata to workflow run steps

Revision ID: 2025_11_27_02
Revises: 2025_11_27_01
Create Date: 2025-11-27 00:00:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "2025_11_27_02"
down_revision = "20251127_010000"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("workflow_run_steps", sa.Column("stage_name", sa.String(), nullable=True))
    op.add_column(
        "workflow_run_steps", sa.Column("parallel_group", sa.String(), nullable=True)
    )
    op.add_column("workflow_run_steps", sa.Column("branch_index", sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column("workflow_run_steps", "branch_index")
    op.drop_column("workflow_run_steps", "parallel_group")
    op.drop_column("workflow_run_steps", "stage_name")
