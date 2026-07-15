from pydantic import BaseModel, ConfigDict


class IncidentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    alert_id: int | None
    title: str
    severity: str
    status: str
    description: str


class IncidentCreate(BaseModel):
    title: str
    severity: str = "medium"
    description: str = ""
    alert_id: int | None = None


class IncidentUpdate(BaseModel):
    status: str  # open | acknowledged | resolved
