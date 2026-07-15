from pydantic import BaseModel, ConfigDict


class AlertRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    source: str
    severity: str
    title: str
    description: str
    status: str
    resolved: bool
    acknowledged_by: str


class NotificationLogRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    channel: str
    recipient: str
    subject: str
    status: str


class AlertmanagerWebhookAlert(BaseModel):
    status: str  # "firing" | "resolved"
    labels: dict[str, str] = {}
    annotations: dict[str, str] = {}


class AlertmanagerWebhookPayload(BaseModel):
    alerts: list[AlertmanagerWebhookAlert] = []


class AcknowledgeRequest(BaseModel):
    acknowledged_by: str = ""


class AlertDashboardSummary(BaseModel):
    active_alerts: int
    critical: int
    warning: int
    resolved_today: int


class AlertStats(BaseModel):
    total: int
    active: int
    resolved: int
    critical: int
    warning: int
