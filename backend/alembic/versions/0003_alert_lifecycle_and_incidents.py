"""phase 2.6 - alert lifecycle (status, acknowledged_by) and incidents.alert_id

Revision ID: 0003
Revises: 0002
Create Date: 2026-07-14

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "alerts",
        sa.Column("status", sa.String(length=20), nullable=False, server_default="active"),
    )
    op.add_column(
        "alerts",
        sa.Column("acknowledged_by", sa.String(length=255), nullable=False, server_default=""),
    )
    # Backfill: any alert already marked resolved should carry status="resolved" too.
    op.execute("UPDATE alerts SET status = 'resolved' WHERE resolved = TRUE")

    op.add_column(
        "incidents",
        sa.Column("alert_id", sa.Integer(), sa.ForeignKey("alerts.id"), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("incidents", "alert_id")
    op.drop_column("alerts", "acknowledged_by")
    op.drop_column("alerts", "status")
