"""phase 2 - monitoring tables (metric_history, pod_metrics, cluster_metrics, jenkins_metrics)

Revision ID: 0002
Revises: 0001
Create Date: 2026-07-11

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "metric_history",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("metric_name", sa.String(length=50), nullable=False, index=True),
        sa.Column("value", sa.Float(), nullable=False),
        sa.Column("unit", sa.String(length=20), nullable=False, server_default=""),
        sa.Column("source", sa.String(length=50), nullable=False, server_default="prometheus"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "pod_metrics",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("pod_name", sa.String(length=255), nullable=False, index=True),
        sa.Column("namespace", sa.String(length=255), nullable=False, server_default="default"),
        sa.Column("node", sa.String(length=255), nullable=False, server_default=""),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="Unknown"),
        sa.Column("restarts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("cpu", sa.String(length=20), nullable=False, server_default=""),
        sa.Column("memory", sa.String(length=20), nullable=False, server_default=""),
        sa.Column("container_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "cluster_metrics",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("cluster_status", sa.String(length=50), nullable=False, server_default="Unknown"),
        sa.Column("nodes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("pods", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("deployments", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("cpu_usage", sa.Float(), nullable=True),
        sa.Column("memory_usage", sa.Float(), nullable=True),
        sa.Column("disk_usage", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "jenkins_metrics",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("job_name", sa.String(length=255), nullable=False, index=True),
        sa.Column("build_number", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="UNKNOWN"),
        sa.Column("duration_ms", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("jenkins_metrics")
    op.drop_table("cluster_metrics")
    op.drop_table("pod_metrics")
    op.drop_table("metric_history")
