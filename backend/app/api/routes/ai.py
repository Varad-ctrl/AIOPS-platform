"""
AI-powered log analysis, root cause analysis, and natural language query
endpoints (Module 5.3).

    GET  /ai/logs/summary?namespace=&pod=&hours=1
    GET  /ai/logs/anomalies?namespace=&pod=&hours=1
    POST /ai/log-analysis              {"namespace"?, "pod"?, "hours"?}
    POST /ai/root-cause                {"incident_id"?, "description"?}
    POST /ai/incidents/{id}/root-cause  (back-compat alias, incident-bound)
    POST /ai/incident-summary           {"incident_id"}
    POST /ai/recommendations
    POST /ai/chat                        {"question"}
    POST /ai/query                        (alias of /ai/chat)
    GET  /ai/chat/history
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.auth.rbac import require_any_role
from app.models.user import User
from app.schemas.ai import (
    AnomalyResponse,
    ChatMessage,
    IncidentSummaryRequest,
    IncidentSummaryResponse,
    LogAnalysisRequest,
    LogAnalysisResponse,
    LogSummaryResponse,
    QueryRequest,
    QueryResponse,
    RecommendationsResponse,
    RootCauseRequest,
    RootCauseResponse,
)
from app.services.insight_service import InsightService

router = APIRouter(prefix="/ai", tags=["AI Insights"])


def get_insight_service(db: Session = Depends(get_db)) -> InsightService:
    return InsightService(db)


@router.get(
    "/logs/summary",
    response_model=LogSummaryResponse,
    summary="AI summary of recent logs for a namespace/pod",
    dependencies=[Depends(require_any_role)],
)
async def summarize_logs(
    namespace: str | None = Query(default=None),
    pod: str | None = Query(default=None),
    hours: int = Query(default=1, ge=1, le=24),
    service: InsightService = Depends(get_insight_service),
):
    return await service.summarize_logs(namespace=namespace, pod=pod, hours=hours)


@router.get(
    "/logs/anomalies",
    response_model=AnomalyResponse,
    summary="AI anomaly detection over recent logs",
    dependencies=[Depends(require_any_role)],
)
async def detect_anomalies(
    namespace: str | None = Query(default=None),
    pod: str | None = Query(default=None),
    hours: int = Query(default=1, ge=1, le=24),
    service: InsightService = Depends(get_insight_service),
):
    return await service.detect_anomalies(namespace=namespace, pod=pod, hours=hours)


@router.post(
    "/log-analysis",
    response_model=LogAnalysisResponse,
    summary="Combined AI summary + anomaly detection over recent logs",
    dependencies=[Depends(require_any_role)],
)
async def log_analysis(
    payload: LogAnalysisRequest = LogAnalysisRequest(),
    service: InsightService = Depends(get_insight_service),
):
    return await service.log_analysis(namespace=payload.namespace, pod=payload.pod, hours=payload.hours)


@router.post(
    "/root-cause",
    response_model=RootCauseResponse,
    summary="Structured root cause analysis (incident-bound or freeform description)",
    dependencies=[Depends(require_any_role)],
)
async def root_cause(
    payload: RootCauseRequest,
    service: InsightService = Depends(get_insight_service),
):
    return await service.root_cause_analysis(
        incident_id=payload.incident_id, description=payload.description
    )


@router.post(
    "/incidents/{incident_id}/root-cause",
    response_model=RootCauseResponse,
    summary="Root cause analysis for a specific incident (persists to analysis_logs)",
    dependencies=[Depends(require_any_role)],
)
async def root_cause_for_incident(
    incident_id: int, service: InsightService = Depends(get_insight_service)
):
    return await service.root_cause_analysis(incident_id=incident_id)


@router.post(
    "/incident-summary",
    response_model=IncidentSummaryResponse,
    summary="AI summary of an incident for a status update",
    dependencies=[Depends(require_any_role)],
)
async def incident_summary(
    payload: IncidentSummaryRequest, service: InsightService = Depends(get_insight_service)
):
    return await service.incident_summary(payload.incident_id)


@router.post(
    "/recommendations",
    response_model=RecommendationsResponse,
    summary="AI-suggested remediation actions based on current alerts/incidents/metrics",
    dependencies=[Depends(require_any_role)],
)
async def recommendations(service: InsightService = Depends(get_insight_service)):
    return await service.recommendations()


@router.post(
    "/chat",
    response_model=QueryResponse,
    summary="Ask a natural-language question about current system state",
    dependencies=[Depends(require_any_role)],
)
async def chat(
    payload: QueryRequest,
    service: InsightService = Depends(get_insight_service),
    current_user: User = Depends(get_current_user),
):
    return await service.answer_query(payload.question, user_id=current_user.id)


@router.post(
    "/query",
    response_model=QueryResponse,
    summary="Alias of /ai/chat, kept for backward compatibility",
    dependencies=[Depends(require_any_role)],
    include_in_schema=False,
)
async def query_alias(
    payload: QueryRequest,
    service: InsightService = Depends(get_insight_service),
    current_user: User = Depends(get_current_user),
):
    return await service.answer_query(payload.question, user_id=current_user.id)


@router.get(
    "/chat/history",
    response_model=list[ChatMessage],
    summary="This user's AI chat history",
    dependencies=[Depends(require_any_role)],
)
def chat_history(
    limit: int = Query(default=50, ge=1, le=200),
    service: InsightService = Depends(get_insight_service),
    current_user: User = Depends(get_current_user),
):
    history = service.get_chat_history(current_user.id, limit=limit)
    return [
        ChatMessage(role=h.role, message=h.message, created_at=h.created_at.isoformat())
        for h in history
    ]
