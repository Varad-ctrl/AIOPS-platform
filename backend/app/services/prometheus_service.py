"""
Thin async client around Prometheus's HTTP API.

Responsibilities (per roadmap Module 2.2):
    - Execute PromQL (instant and range queries)
    - Parse Prometheus responses into plain Python values
    - Handle time ranges for historical/charting data
    - Handle query failures without crashing the API (returns None/[] and
      lets the route layer decide how to respond)
"""
import math
from datetime import UTC, datetime, timedelta
from typing import Any

import httpx

from app.core.config import settings
from app.core.logging_config import get_logger

logger = get_logger("prometheus_service")

# Canonical PromQL expressions for the metrics this platform tracks.
# Centralized here so the API layer stays free of raw PromQL strings.
#
# Every expression is wrapped in an aggregation (avg/sum) with no `by(...)`
# clause, so it always resolves to exactly one time series - regardless of
# how many nodes, filesystems, or network interfaces are being scraped.
# Without this, a query like `node_load1` on a 3-node cluster returns 3
# series, and instant_query()/range_query() would silently pick whichever
# one Prometheus happens to return first. That's the "Windows-specific
# mount point" style fragility - aggregating up front makes these queries
# portable across a single Docker Desktop host, WSL, bare Linux, Kind, and
# OpenShift alike.
QUERIES = {
    "cpu": '100 - (avg(rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)',
    "memory": "avg((1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100)",
   "disk": (
    '100 * ('
    '1 - ('
    'node_filesystem_avail_bytes{'
    'mountpoint="/var/lib",'
    'fstype="ext4"}'
    '/'
    'node_filesystem_size_bytes{'
    'mountpoint="/var/lib",'
    'fstype="ext4"}'
    ')'
    ')'
),
    "network": (
        "sum(rate(node_network_receive_bytes_total{device!~\"lo\"}[5m])) + "
        "sum(rate(node_network_transmit_bytes_total{device!~\"lo\"}[5m]))"
    ),
    "load": "avg(node_load1)",
    "filesystem": (
        'avg(node_filesystem_avail_bytes{fstype!~"tmpfs|overlay"}) / 1024 / 1024 / 1024'
    ),
}

UNITS = {
    "cpu": "%",
    "memory": "%",
    "disk": "%",
    "network": "bytes/s",
    "load": "load",
    "filesystem": "GB",
}


class PrometheusService:
    def __init__(self, base_url: str | None = None, timeout: float = 5.0):
        self.base_url = (base_url or settings.PROMETHEUS_URL).rstrip("/")
        self.timeout = timeout

    async def _get(self, path: str, params: dict[str, Any]) -> dict[str, Any] | None:
        url = f"{self.base_url}{path}"
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as exc:
            logger.warning("prometheus_query_failed", url=url, params=params, error=str(exc))
            return None

    async def instant_query(self, promql: str) -> float | None:
     """Run an instant PromQL query, return the first scalar result."""

     data = await self._get("/api/v1/query", {"query": promql})

     if not data or data.get("status") != "success":
        return None

     result = data.get("data", {}).get("result", [])
     if not result:
        return None

     try:
        value = float(result[0]["value"][1])

        # Handle NaN and Infinity
        if math.isnan(value) or math.isinf(value):
            logger.warning(
                "Invalid Prometheus value",
                query=promql,
                value=result[0]["value"][1],
            )
            return None

        return round(value, 2)

     except (KeyError, IndexError, ValueError, TypeError):
        return None

    async def range_query(
        self, promql: str, start: datetime, end: datetime, step: str = "60s"
    ) -> list[dict[str, Any]]:
        """
        Run a PromQL range query and return [{"timestamp": iso, "value": float}, ...]
        ready for direct use in frontend charting libraries.
        """
        data = await self._get(
            "/api/v1/query_range",
            {
                "query": promql,
                "start": start.timestamp(),
                "end": end.timestamp(),
                "step": step,
            },
        )
        if not data or data.get("status") != "success":
            return []

        result = data.get("data", {}).get("result", [])
        if not result:
            return []

        points = []
        for timestamp, value in result[0].get("values", []):
            try:
                points.append(
                    {
                        "timestamp": datetime.fromtimestamp(
                            float(timestamp), tz=UTC
                        ).isoformat(),
                        "value": round(float(value), 2),
                    }
                )
            except (ValueError, TypeError):
                continue
        return points

    async def get_metric(self, metric_name: str) -> dict[str, Any]:
        """Fetch a named metric (cpu/memory/disk/network/load/filesystem)."""
        promql = QUERIES.get(metric_name)
        if promql is None:
            raise ValueError(f"Unknown metric '{metric_name}'")

        value = await self.instant_query(promql)
        return {
            "metric": metric_name,
            "value": value,
            "unit": UNITS[metric_name],
            "available": value is not None,
        }

    async def get_metric_history(
        self, metric_name: str, hours: int = 24, step: str = "5m"
    ) -> list[dict[str, Any]]:
        promql = QUERIES.get(metric_name)
        if promql is None:
            raise ValueError(f"Unknown metric '{metric_name}'")

        end = datetime.now(UTC)
        start = end - timedelta(hours=hours)
        return await self.range_query(promql, start, end, step)

    async def targets_up(self) -> dict[str, Any]:
        """Used by /cluster/health and dashboard status widgets."""
        data = await self._get("/api/v1/targets", {})
        if not data or data.get("status") != "success":
            return {"up": 0, "total": 0}

        active = data.get("data", {}).get("activeTargets", [])
        up = sum(1 for t in active if t.get("health") == "up")
        return {"up": up, "total": len(active)}
