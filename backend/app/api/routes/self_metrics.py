"""
Exposes the backend's own process metrics in Prometheus text format at
GET /api/v1/metrics/prometheus - this is what monitoring/prometheus/prometheus.yml
scrapes for the "aiops-backend" job. Kept in a separate module from
metrics.py so the human-facing /metrics/{cpu,memory,...} routes and this
machine-facing exposition endpoint don't collide on the /metrics prefix.
"""
from fastapi import APIRouter, Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

router = APIRouter(tags=["Metrics"])


@router.get("/metrics/prometheus", summary="Prometheus scrape target for this backend")
def prometheus_exposition():
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
