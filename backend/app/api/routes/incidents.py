"""
Incident management endpoints.

    GET  /incidents                    - list, optionally filtered by status
    GET  /incidents/{id}                - single incident
    POST /incidents                      - create directly
    POST /incidents/from-alert/{alert_id} - promote an existing alert to an incident
    PATCH /incidents/{id}                  - update status (open -> acknowledged -> resolved)
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.auth.rbac import require_any_role, require_devops_or_admin
from app.schemas.incidents import IncidentCreate, IncidentRead, IncidentUpdate
from app.services.incident_service import (
    IncidentNotFoundError,
    IncidentService,
    InvalidIncidentStatusError,
)

router = APIRouter(prefix="/incidents", tags=["Incidents"])


def get_incident_service(db: Session = Depends(get_db)) -> IncidentService:
    return IncidentService(db)


@router.get(
    "",
    response_model=list[IncidentRead],
    summary="List incidents, optionally filtered by status",
    dependencies=[Depends(require_any_role)],
)
def list_incidents(
    status_: str | None = Query(default=None, alias="status"),
    service: IncidentService = Depends(get_incident_service),
):
    return service.list_incidents(status=status_)


@router.get(
    "/{incident_id}",
    response_model=IncidentRead,
    summary="Get a single incident",
    dependencies=[Depends(require_any_role)],
)
def get_incident(incident_id: int, service: IncidentService = Depends(get_incident_service)):
    try:
        return service.get_incident(incident_id)
    except IncidentNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post(
    "",
    response_model=IncidentRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create an incident directly",
    dependencies=[Depends(require_devops_or_admin)],
)
def create_incident(payload: IncidentCreate, service: IncidentService = Depends(get_incident_service)):
    return service.create_incident(
        title=payload.title,
        severity=payload.severity,
        description=payload.description,
        alert_id=payload.alert_id,
    )


@router.post(
    "/from-alert/{alert_id}",
    response_model=IncidentRead,
    status_code=status.HTTP_201_CREATED,
    summary="Promote an existing alert to an incident",
    dependencies=[Depends(require_devops_or_admin)],
)
def promote_alert(alert_id: int, service: IncidentService = Depends(get_incident_service)):
    try:
        return service.promote_alert(alert_id)
    except IncidentNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.patch(
    "/{incident_id}",
    response_model=IncidentRead,
    summary="Update an incident's status",
    dependencies=[Depends(require_devops_or_admin)],
)
def update_incident(
    incident_id: int, payload: IncidentUpdate, service: IncidentService = Depends(get_incident_service)
):
    try:
        return service.update_status(incident_id, payload.status)
    except IncidentNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except InvalidIncidentStatusError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
