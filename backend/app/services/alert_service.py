"""
Alert business logic (Module 2.9 - Alert Management, Module 2.10 - Email
Notifications, Module 2.6 - lifecycle/search/dashboard/stats).

Lifecycle: active -> acknowledged -> resolved. `resolved` (bool) is kept in
sync with `status == "resolved"` so any existing code that only cares about
open-vs-closed keeps working unchanged.

Two ways alerts are created:
    1. `evaluate_thresholds()` - polls Prometheus metrics directly and
       raises alerts when they cross the thresholds from the roadmap
       (CPU > 90%, Memory > 90%, Disk > 85%).
    2. `handle_alertmanager_webhook()` - receives push notifications from
       Alertmanager itself (which evaluates the same thresholds server-side
       via alert_rules.yml) so alerts fire even if nobody is polling.

Either path converges on `_raise_alert()`, which: saves the alert, sends an
email, and logs the notification.
"""
from datetime import datetime, time, timezone

from sqlalchemy.orm import Session

from app.core.logging_config import get_logger
from app.models.operations import Alert, NotificationLog
from app.services.email_service import EmailService, build_alert_email
from app.services.prometheus_service import PrometheusService

logger = get_logger("alert_service")

THRESHOLDS = {
    "cpu": 90.0,
    "memory": 90.0,
    "disk": 85.0,
}

OPEN_STATUSES = ("active", "acknowledged")


class AlertNotFoundError(Exception):
    pass


class AlertService:
    def __init__(self, db: Session, notify_email: str | None = None):
        self.db = db
        self.prometheus = PrometheusService()
        self.email = EmailService()
        self.notify_email = notify_email

    # --- Reads -----------------------------------------------------------

    def list_alerts(
        self,
        *,
        active_only: bool = False,
        severity: str | None = None,
        source: str | None = None,
        resolved: bool | None = None,
        status: str | None = None,
        start: datetime | None = None,
        end: datetime | None = None,
    ) -> list[Alert]:
        """Search/filter alerts (Module 2.6.1). All filters are optional and
        combine with AND. `active_only` is a shorthand for status IN (active, acknowledged)."""
        query = self.db.query(Alert)

        if active_only:
            query = query.filter(Alert.status.in_(OPEN_STATUSES))
        if severity:
            query = query.filter(Alert.severity == severity)
        if source:
            query = query.filter(Alert.source == source)
        if resolved is not None:
            query = query.filter(Alert.resolved.is_(resolved))
        if status:
            query = query.filter(Alert.status == status)
        if start:
            query = query.filter(Alert.created_at >= start)
        if end:
            query = query.filter(Alert.created_at <= end)

        return query.order_by(Alert.created_at.desc()).all()

    def get_alert(self, alert_id: int) -> Alert:
        alert = self.db.query(Alert).filter(Alert.id == alert_id).first()
        if not alert:
            raise AlertNotFoundError(f"Alert {alert_id} not found")
        return alert

    def dashboard_summary(self) -> dict:
        """Module 2.6.2 - GET /alerts/dashboard"""
        open_alerts = self.db.query(Alert).filter(Alert.status.in_(OPEN_STATUSES)).all()
        today_start = datetime.combine(
            datetime.now(timezone.utc).date(), time.min, tzinfo=timezone.utc
        )
        resolved_today = (
            self.db.query(Alert)
            .filter(Alert.status == "resolved", Alert.updated_at >= today_start)
            .count()
        )

        return {
            "active_alerts": len(open_alerts),
            "critical": sum(1 for a in open_alerts if a.severity == "critical"),
            "warning": sum(1 for a in open_alerts if a.severity in ("warning", "high")),
            "resolved_today": resolved_today,
        }

    def stats(self) -> dict:
        """Module 2.6.3 - GET /alerts/stats"""
        all_alerts = self.db.query(Alert).all()
        return {
            "total": len(all_alerts),
            "active": sum(1 for a in all_alerts if a.status in OPEN_STATUSES),
            "resolved": sum(1 for a in all_alerts if a.status == "resolved"),
            "critical": sum(1 for a in all_alerts if a.severity == "critical"),
            "warning": sum(1 for a in all_alerts if a.severity in ("warning", "high")),
        }

    # --- Lifecycle transitions (Module 2.6.4) -----------------------------

    def acknowledge(self, alert_id: int, acknowledged_by: str = "") -> Alert:
        alert = self.get_alert(alert_id)
        if alert.status == "resolved":
            return alert  # resolved alerts can't be re-acknowledged
        alert.status = "acknowledged"
        alert.acknowledged_by = acknowledged_by
        self.db.commit()
        self.db.refresh(alert)
        logger.info("alert_acknowledged", alert_id=alert_id, by=acknowledged_by)
        return alert

    def resolve(self, alert_id: int) -> Alert:
        alert = self.get_alert(alert_id)
        alert.status = "resolved"
        alert.resolved = True
        self.db.commit()
        self.db.refresh(alert)
        logger.info("alert_resolved", alert_id=alert_id)
        return alert

    # --- Writes ------------------------------------------------------------

    def _raise_alert(self, *, source: str, severity: str, title: str, description: str) -> Alert:
        existing = (
            self.db.query(Alert)
            .filter(
                Alert.source == source,
                Alert.title == title,
                Alert.status.in_(OPEN_STATUSES),
            )
            .first()
        )
        if existing:
            return existing

        alert = Alert(
            source=source,
            severity=severity,
            title=title,
            description=description,
            status="active",
            resolved=False,
        )
        self.db.add(alert)
        self.db.commit()
        self.db.refresh(alert)

        logger.warning("alert_raised", source=source, severity=severity, title=title)

        if self.notify_email:
            subject, body = build_alert_email(title, severity, description, source)
            sent = self.email.send_email(self.notify_email, subject, body)
            log = NotificationLog(
                channel="email",
                recipient=self.notify_email,
                subject=subject,
                status="sent" if sent else "failed",
            )
            self.db.add(log)
            self.db.commit()

        return alert

    async def evaluate_thresholds(self) -> list:
        """Poll Prometheus for cpu/memory/disk and raise alerts on breach."""
        raised = []
        for metric_name, threshold in THRESHOLDS.items():
            metric = await self.prometheus.get_metric(metric_name)
            value = metric.get("value")
            if value is None or value <= threshold:
                continue
            alert = self._raise_alert(
                source="prometheus",
                severity="critical" if value >= threshold + 5 else "high",
                title=f"{metric_name.upper()} usage above {threshold:.0f}%",
                description=f"Current {metric_name} usage is {value}% (threshold: {threshold}%).",
            )
            raised.append(alert)
        return raised

    def handle_alertmanager_webhook(self, payload) -> list:
        raised = []
        for item in payload.alerts:
            title = item.labels.get("alertname", "Unknown alert")
            severity = item.labels.get("severity", "warning")
            description = item.annotations.get("description") or item.annotations.get(
                "summary", ""
            )

            if item.status == "resolved":
                existing = (
                    self.db.query(Alert)
                    .filter(Alert.title == title, Alert.status.in_(OPEN_STATUSES))
                    .first()
                )
                if existing:
                    existing.status = "resolved"
                    existing.resolved = True
                    self.db.commit()
                continue

            alert = self._raise_alert(
                source="alertmanager",
                severity=severity,
                title=title,
                description=description,
            )
            raised.append(alert)
        return raised
