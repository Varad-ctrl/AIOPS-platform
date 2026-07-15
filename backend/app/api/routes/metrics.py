"""
Live and historical infrastructure metrics.

    GET /metrics/{cpu|memory|disk|network|load|filesystem}
    GET /metrics/history/{cpu|memory|disk|network|load|filesystem}?hours=24
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.auth.rbac import require_any_role
from app.schemas.metrics import MetricHistoryPoint, MetricValue
from app.services.prometheus_service import PrometheusService

router = APIRouter(prefix="/metrics", tags=["Metrics"])

VALID_METRICS = {"cpu", "memory", "disk", "network", "load", "filesystem"}
# History is available for every metric the service exposes - the query map
# in prometheus_service.QUERIES already covers all six, so there's no
# reason to gate history to a subset of them.
VALID_HISTORY_METRICS = VALID_METRICS


def get_prometheus_service() -> PrometheusService:
    return PrometheusService()


@router.get(
    "/{metric_name}",
    response_model=MetricValue,
    summary="Current value of a single metric",
    dependencies=[Depends(require_any_role)],
)
async def get_metric(
    metric_name: str,
    prometheus: PrometheusService = Depends(get_prometheus_service),
):
    if metric_name not in VALID_METRICS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Unknown metric '{metric_name}'. Valid options: {sorted(VALID_METRICS)}",
        )
    return await prometheus.get_metric(metric_name)


@router.get(
    "/history/{metric_name}",
    response_model=list[MetricHistoryPoint],
    summary="Historical values of a metric, suitable for charting",
    dependencies=[Depends(require_any_role)],
)
async def get_metric_history(
    metric_name: str,
    hours: int = Query(default=24, ge=1, le=168, description="Lookback window in hours"),
    step: str = Query(default="5m", description="Prometheus step, e.g. '1m', '5m', '1h'"),
    prometheus: PrometheusService = Depends(get_prometheus_service),
):
    if metric_name not in VALID_HISTORY_METRICS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"History not available for '{metric_name}'. "
            f"Valid options: {sorted(VALID_HISTORY_METRICS)}",
        )
    return await prometheus.get_metric_history(metric_name, hours=hours, step=step)
