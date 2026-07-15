"""
Alert management endpoints.

    GET  /alerts                - all alerts, with optional search/filter
    GET  /alerts/active          - unresolved alerts only (shorthand filter)
    GET  /alerts/history          - alias of GET /alerts, explicit per roadmap
    GET  /alerts/dashboard         - summary counts for dashboard widgets
    GET  /alerts/stats              - overall alert statistics
    POST /alerts/{id}/acknowledge    - active -> acknowledged
    POST /alerts/{id}/resolve         - -> resolved
    POST /alerts/webhook               - receiver for Alertmanager push notifications
"""
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.auth.rbac import require_any_role, require_devops_or_admin
from app.core.config import settings
from app.core.logging_config import get_logger
from app.models.user import User
from app.schemas.alerts import (
    AcknowledgeRequest,
    AlertDashboardSummary,
    AlertmanagerWebhookPayload,
    AlertRead,
    AlertStats,
)
from app.services.alert_service import AlertNotFoundError, AlertService

router = APIRouter(prefix="/alerts", tags=["Alerts"])
logger = get_logger("alerts_routes")


def get_alert_service(db: Session = Depends(get_db)) -> AlertService:
    notify_email = settings.SMTP_FROM_EMAIL if settings.SMTP_HOST else None
    return AlertService(db, notify_email=notify_email)


@router.get(
    "",
    response_model=list[AlertRead],
    summary="List alerts, with optional search/filter",
    dependencies=[Depends(require_any_role)],
)
def list_alerts(
    severity: str | None = Query(default=None, description="e.g. critical, high, warning, low"),
    source: str | None = Query(default=None, description="e.g. prometheus, alertmanager"),
    resolved: bool | None = Query(default=None),
    status_: str | None = Query(default=None, alias="status", description="active | acknowledged | resolved"),
    start: datetime | None = Query(default=None, description="ISO 8601, filters created_at >="),
    end: datetime | None = Query(default=None, description="ISO 8601, filters created_at <="),
    service: AlertService = Depends(get_alert_service),
):
    return service.list_alerts(
        severity=severity, source=source, resolved=resolved, status=status_, start=start, end=end
    )


@router.get(
    "/active",
    response_model=list[AlertRead],
    summary="List active (unresolved: active or acknowledged) alerts",
    dependencies=[Depends(require_any_role)],
)
def list_active_alerts(service: AlertService = Depends(get_alert_service)):
    return service.list_alerts(active_only=True)


@router.get(
    "/history",
    response_model=list[AlertRead],
    summary="Alert history",
    dependencies=[Depends(require_any_role)],
)
def list_alert_history(service: AlertService = Depends(get_alert_service)):
    return service.list_alerts()


@router.get(
    "/dashboard",
    response_model=AlertDashboardSummary,
    summary="Summary counts for dashboard widgets",
    dependencies=[Depends(require_any_role)],
)
def alert_dashboard(service: AlertService = Depends(get_alert_service)):
    return service.dashboard_summary()


@router.get(
    "/stats",
    response_model=AlertStats,
    summary="Overall alert statistics",
    dependencies=[Depends(require_any_role)],
)
def alert_stats(service: AlertService = Depends(get_alert_service)):
    return service.stats()


@router.post(
    "/{alert_id}/acknowledge",
    response_model=AlertRead,
    summary="Acknowledge an active alert (active -> acknowledged)",
    dependencies=[Depends(require_devops_or_admin)],
)
def acknowledge_alert(
    alert_id: int,
    payload: AcknowledgeRequest = AcknowledgeRequest(),
    service: AlertService = Depends(get_alert_service),
    current_user: User = Depends(get_current_user),
):
    try:
        return service.acknowledge(alert_id, acknowledged_by=payload.acknowledged_by or current_user.email)
    except AlertNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post(
    "/{alert_id}/resolve",
    response_model=AlertRead,
    summary="Manually resolve an alert",
    dependencies=[Depends(require_devops_or_admin)],
)
def resolve_alert(alert_id: int, service: AlertService = Depends(get_alert_service)):
    try:
        return service.resolve(alert_id)
    except AlertNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post(
    "/webhook",
    summary="Receiver for Alertmanager webhook notifications",
    include_in_schema=True,
)
async def alertmanager_webhook(request: Request, service: AlertService = Depends(get_alert_service)):
    body = await request.json()
    payload = AlertmanagerWebhookPayload.model_validate(body)
    raised = service.handle_alertmanager_webhook(payload)
    logger.info("alertmanager_webhook_processed", alerts_raised=len(raised))
    return {"received": True, "alerts_raised": len(raised)}
