"""
Persistence models for Phase 2 monitoring data:

    metric_history   -> time series of node-level metrics (cpu/memory/disk/...)
    pod_metrics      -> point-in-time snapshots of pod resource usage
    cluster_metrics  -> point-in-time snapshots of overall cluster health
    jenkins_metrics  -> build history snapshots
"""
from sqlalchemy import Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base_class import Base


class MetricHistory(Base):
    __tablename__ = "metric_history"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    metric_name: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    value: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[str] = mapped_column(String(20), nullable=False, default="")
    source: Mapped[str] = mapped_column(String(50), nullable=False, default="prometheus")


class PodMetric(Base):
    __tablename__ = "pod_metrics"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    pod_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    namespace: Mapped[str] = mapped_column(String(255), nullable=False, default="default")
    node: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="Unknown")
    restarts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    cpu: Mapped[str] = mapped_column(String(20), nullable=False, default="")
    memory: Mapped[str] = mapped_column(String(20), nullable=False, default="")
    container_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class ClusterMetric(Base):
    __tablename__ = "cluster_metrics"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    cluster_status: Mapped[str] = mapped_column(String(50), nullable=False, default="Unknown")
    nodes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    pods: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    deployments: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    cpu_usage: Mapped[float] = mapped_column(Float, nullable=True)
    memory_usage: Mapped[float] = mapped_column(Float, nullable=True)
    disk_usage: Mapped[float] = mapped_column(Float, nullable=True)


class JenkinsMetric(Base):
    __tablename__ = "jenkins_metrics"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    job_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    build_number: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="UNKNOWN")
    duration_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
