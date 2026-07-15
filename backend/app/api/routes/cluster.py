"""
GET /cluster/health - single-call cluster overview combining Kubernetes
object counts with Prometheus resource-usage percentages.
"""
from fastapi import APIRouter, Depends

from app.auth.rbac import require_any_role
from app.schemas.metrics import ClusterHealth
from app.services.kubernetes_service import KubernetesService
from app.services.prometheus_service import PrometheusService

router = APIRouter(prefix="/cluster", tags=["Cluster"])


@router.get(
    "/health",
    response_model=ClusterHealth,
    summary="Aggregate cluster health snapshot",
    dependencies=[Depends(require_any_role)],
)
async def cluster_health():
    k8s = KubernetesService()
    prometheus = PrometheusService()

    summary = k8s.cluster_summary()
    cpu = await prometheus.get_metric("cpu")
    memory = await prometheus.get_metric("memory")
    disk = await prometheus.get_metric("disk")

    return ClusterHealth(
        cluster=summary["cluster"],
        nodes=summary["nodes"],
        pods=summary["pods"],
        deployments=summary["deployments"],
        cpu_usage=cpu["value"],
        memory_usage=memory["value"],
        disk_usage=disk["value"],
    )
