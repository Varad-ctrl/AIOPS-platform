"""
Log search and retrieval endpoints, backed by Loki (Module 3.2, extended
per Module 4.4).

    GET /logs                          -> alias of /logs/recent
    GET /logs/recent?limit=100&hours=1
    GET /logs/search?query=&namespace=&pod=&container=&service=&severity=&hours=1&limit=200
    GET /logs/pods/{pod}?hours=1&limit=200
    GET /logs/containers/{container}?hours=1&limit=200
    GET /logs/errors?hours=1&limit=200
    GET /logs/labels/{label}            -> distinct values, powers filter dropdowns
"""
from fastapi import APIRouter, Depends, Query

from app.auth.rbac import require_any_role
from app.schemas.logs import LogSearchResponse
from app.services.loki_service import LokiService

router = APIRouter(prefix="/logs", tags=["Logs"])


def get_loki_service() -> LokiService:
    return LokiService()


async def _build_response(loki: LokiService, fetch) -> LogSearchResponse:
    reachable = await loki.is_reachable()
    items = await fetch() if reachable else []
    return LogSearchResponse(available=reachable, count=len(items), items=items)


@router.get(
    "",
    response_model=LogSearchResponse,
    summary="Recent logs (alias of /logs/recent)",
    dependencies=[Depends(require_any_role)],
)
async def logs_root(
    limit: int = Query(default=100, ge=1, le=1000),
    hours: int = Query(default=1, ge=1, le=168),
    loki: LokiService = Depends(get_loki_service),
):
    return await _build_response(loki, lambda: loki.recent(limit=limit, hours=hours))


@router.get(
    "/recent",
    response_model=LogSearchResponse,
    summary="Most recent log lines across all sources",
    dependencies=[Depends(require_any_role)],
)
async def recent_logs(
    limit: int = Query(default=100, ge=1, le=1000),
    hours: int = Query(default=1, ge=1, le=168),
    loki: LokiService = Depends(get_loki_service),
):
    return await _build_response(loki, lambda: loki.recent(limit=limit, hours=hours))


@router.get(
    "/search",
    response_model=LogSearchResponse,
    summary="Search logs with optional filters (namespace, pod, severity, free text)",
    dependencies=[Depends(require_any_role)],
)
async def search_logs(
    query: str | None = Query(default=None, description="Free-text search term"),
    namespace: str | None = Query(default=None),
    pod: str | None = Query(default=None),
    container: str | None = Query(default=None),
    service: str | None = Query(default=None),
    severity: str | None = Query(default=None, description="e.g. error, warn, info"),
    hours: int = Query(default=1, ge=1, le=168),
    limit: int = Query(default=200, ge=1, le=1000),
    loki: LokiService = Depends(get_loki_service),
):
    return await _build_response(
        loki,
        lambda: loki.search(
            search=query,
            namespace=namespace,
            pod=pod,
            container=container,
            service=service,
            severity=severity,
            hours=hours,
            limit=limit,
        ),
    )


@router.get(
    "/pods/{pod}",
    response_model=LogSearchResponse,
    summary="Logs for a specific pod",
    dependencies=[Depends(require_any_role)],
)
async def logs_for_pod(
    pod: str,
    hours: int = Query(default=1, ge=1, le=168),
    limit: int = Query(default=200, ge=1, le=1000),
    loki: LokiService = Depends(get_loki_service),
):
    return await _build_response(loki, lambda: loki.logs_for_pod(pod, hours=hours, limit=limit))


@router.get(
    "/containers/{container}",
    response_model=LogSearchResponse,
    summary="Logs for a specific container",
    dependencies=[Depends(require_any_role)],
)
async def logs_for_container(
    container: str,
    hours: int = Query(default=1, ge=1, le=168),
    limit: int = Query(default=200, ge=1, le=1000),
    loki: LokiService = Depends(get_loki_service),
):
    return await _build_response(
        loki, lambda: loki.logs_for_container(container, hours=hours, limit=limit)
    )


@router.get(
    "/errors",
    response_model=LogSearchResponse,
    summary="Error-level logs only, across all sources",
    dependencies=[Depends(require_any_role)],
)
async def error_logs(
    hours: int = Query(default=1, ge=1, le=168),
    limit: int = Query(default=200, ge=1, le=1000),
    loki: LokiService = Depends(get_loki_service),
):
    return await _build_response(loki, lambda: loki.errors_only(hours=hours, limit=limit))


@router.get(
    "/labels/{label}",
    summary="Distinct values for a Loki label (e.g. container, service, level)",
    dependencies=[Depends(require_any_role)],
)
async def label_values(label: str, loki: LokiService = Depends(get_loki_service)):
    reachable = await loki.is_reachable()
    values = await loki.label_values(label) if reachable else []
    return {"available": reachable, "label": label, "values": values}
