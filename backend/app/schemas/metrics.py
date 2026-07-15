"""
Schemas for the /metrics API surface.
"""
from pydantic import BaseModel


class MetricValue(BaseModel):
    metric: str
    value: float | None
    unit: str
    available: bool


class MetricHistoryPoint(BaseModel):
    timestamp: str
    value: float


class ClusterHealth(BaseModel):
    cluster: str
    nodes: int
    pods: int
    deployments: int
    cpu_usage: float | None
    memory_usage: float | None
    disk_usage: float | None
