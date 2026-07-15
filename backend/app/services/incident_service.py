"""
Incident business logic. Incidents are deliberately kept separate from
Alerts: an Alert is a raw signal (one Prometheus/Alertmanager firing), an
Incident is the thing a human is actually tracking and resolving - which
may be opened directly, or promoted from a related alert.

    Alert (raw signal) --promote--> Incident (open) -> acknowledged -> resolved
"""
from sqlalchemy.orm import Session

from app.core.logging_config import get_logger
from app.models.operations import Alert, Incident

logger = get_logger("incident_service")

VALID_STATUSES = ("open", "acknowledged", "resolved")


class IncidentNotFoundError(Exception):
    pass


class InvalidIncidentStatusError(Exception):
    pass


class IncidentService:
    def __init__(self, db: Session):
        self.db = db

    def list_incidents(self, *, status: str | None = None) -> list[Incident]:
        query = self.db.query(Incident)
        if status:
            query = query.filter(Incident.status == status)
        return query.order_by(Incident.created_at.desc()).all()

    def get_incident(self, incident_id: int) -> Incident:
        incident = self.db.query(Incident).filter(Incident.id == incident_id).first()
        if not incident:
            raise IncidentNotFoundError(f"Incident {incident_id} not found")
        return incident

    def create_incident(
        self,
        *,
        title: str,
        severity: str = "medium",
        description: str = "",
        alert_id: int | None = None,
    ) -> Incident:
        incident = Incident(
            title=title,
            severity=severity,
            description=description,
            alert_id=alert_id,
            status="open",
        )
        self.db.add(incident)
        self.db.commit()
        self.db.refresh(incident)
        logger.info("incident_created", title=title, severity=severity, alert_id=alert_id)
        return incident

    def promote_alert(self, alert_id: int) -> Incident:
        """Create an Incident from an existing Alert (idempotent)."""
        alert = self.db.query(Alert).filter(Alert.id == alert_id).first()
        if not alert:
            raise IncidentNotFoundError(f"Alert {alert_id} not found")

        existing = self.db.query(Incident).filter(Incident.alert_id == alert_id).first()
        if existing:
            return existing

        return self.create_incident(
            title=alert.title,
            severity=alert.severity,
            description=alert.description,
            alert_id=alert.id,
        )

    def update_status(self, incident_id: int, status: str) -> Incident:
        if status not in VALID_STATUSES:
            raise InvalidIncidentStatusError(
                f"Invalid status '{status}'. Valid options: {VALID_STATUSES}"
            )
        incident = self.get_incident(incident_id)
        incident.status = status
        self.db.commit()
        self.db.refresh(incident)
        logger.info("incident_status_updated", incident_id=incident_id, status=status)
        return incident
