"""
Thin async client around Loki's HTTP API (Module 3.1/3.2, extended for
Module 4.4's per-pod/per-container/errors-only endpoints).

Mirrors the shape of prometheus_service.py deliberately: same graceful
degradation (returns [] instead of raising when Loki is unreachable), same
"build a query, execute it, parse the response" structure.

LogQL primer for anyone reading this file cold:
    {label="value"}              -> stream selector (required)
    {label="value"} |= "text"    -> line contains "text"
    {label="value"} | level="error"  -> filter on an extracted label
"""
from datetime import UTC, datetime, timedelta
from typing import Any

import httpx

from app.core.config import settings
from app.core.logging_config import get_logger

logger = get_logger("loki_service")


class LokiService:
    def __init__(self, base_url: str | None = None, timeout: float = 5.0):
        self.base_url = (base_url or settings.LOKI_URL).rstrip("/")
        self.timeout = timeout

    async def _get(self, path: str, params: dict[str, Any]) -> dict[str, Any] | None:
        url = f"{self.base_url}{path}"
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as exc:
            logger.warning("loki_query_failed", url=url, params=params, error=str(exc))
            return None

    @staticmethod
    def build_query(
        *,
        namespace: str | None = None,
        pod: str | None = None,
        container: str | None = None,
        service: str | None = None,
        severity: str | None = None,
        search: str | None = None,
    ) -> str:
        """Builds a LogQL query from human-friendly filters.

        Falls back to a container-name selector (Docker Compose labels) when
        no namespace/pod is given, since this stack's default log source is
        Promtail scraping Docker containers, not a Kubernetes cluster.
        """
        selectors: list[str] = []
        if namespace:
            selectors.append(f'namespace="{namespace}"')
        if pod:
            selectors.append(f'pod=~"{pod}.*"')
        if container:
            selectors.append(f'container=~"{container}.*"')
        if service:
            selectors.append(f'service=~"{service}.*"')

        if not selectors:
            # No specific target - match every stream Promtail is shipping.
            selectors.append('project="aiops-assistant"')

        query = "{" + ", ".join(selectors) + "}"

        if severity:
            query += f' | level="{severity.lower()}"'
        if search:
            escaped = search.replace('"', '\\"')
            query += f' |= "{escaped}"'

        return query

    async def query_range(
        self,
        query: str,
        *,
        start: datetime | None = None,
        end: datetime | None = None,
        limit: int = 200,
        direction: str = "backward",
    ) -> list[dict[str, Any]]:
        """Runs a LogQL range query, returns entries newest-first by default."""
        end = end or datetime.now(UTC)
        start = start or (end - timedelta(hours=1))

        data = await self._get(
            "/loki/api/v1/query_range",
            {
                "query": query,
                "start": int(start.timestamp() * 1e9),
                "end": int(end.timestamp() * 1e9),
                "limit": limit,
                "direction": direction,
            },
        )
        if not data or data.get("status") != "success":
            return []

        entries: list[dict[str, Any]] = []
        for stream in data.get("data", {}).get("result", []):
            labels = stream.get("stream", {})
            for ts_ns, line in stream.get("values", []):
                entries.append(
                    {
                        "timestamp": datetime.fromtimestamp(
                            int(ts_ns) / 1e9, tz=UTC
                        ).isoformat(),
                        "message": line,
                        "labels": labels,
                    }
                )

        entries.sort(key=lambda e: e["timestamp"], reverse=(direction == "backward"))
        return entries[:limit]

    async def recent(self, limit: int = 100, hours: int = 1) -> list[dict[str, Any]]:
        query = self.build_query()
        return await self.query_range(
            query,
            start=datetime.now(UTC) - timedelta(hours=hours),
            limit=limit,
        )

    async def search(
        self,
        *,
        search: str | None = None,
        namespace: str | None = None,
        pod: str | None = None,
        container: str | None = None,
        service: str | None = None,
        severity: str | None = None,
        hours: int = 1,
        limit: int = 200,
    ) -> list[dict[str, Any]]:
        query = self.build_query(
            namespace=namespace,
            pod=pod,
            container=container,
            service=service,
            severity=severity,
            search=search,
        )
        return await self.query_range(
            query,
            start=datetime.now(UTC) - timedelta(hours=hours),
            limit=limit,
        )

    async def logs_for_pod(self, pod: str, hours: int = 1, limit: int = 200) -> list[dict[str, Any]]:
        return await self.search(pod=pod, hours=hours, limit=limit)

    async def logs_for_container(
        self, container: str, hours: int = 1, limit: int = 200
    ) -> list[dict[str, Any]]:
        return await self.search(container=container, hours=hours, limit=limit)

    async def errors_only(self, hours: int = 1, limit: int = 200) -> list[dict[str, Any]]:
        return await self.search(severity="error", hours=hours, limit=limit)

    async def label_values(self, label: str) -> list[str]:
        """Powers filter dropdowns in the UI (e.g. list of known containers)."""
        data = await self._get(f"/loki/api/v1/label/{label}/values", {})
        if not data or data.get("status") != "success":
            return []
        return data.get("data", [])

    async def is_reachable(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.base_url}/ready")
                return response.status_code == 200
        except httpx.HTTPError:
            return False
