from pydantic import BaseModel


class LogSummaryResponse(BaseModel):
    available: bool
    summary: str
    log_count: int


class AnomalyResponse(BaseModel):
    available: bool
    findings: str
    log_count: int


class LogAnalysisRequest(BaseModel):
    namespace: str | None = None
    pod: str | None = None
    hours: int = 1


class LogAnalysisResponse(BaseModel):
    available: bool
    summary: str
    findings: str
    log_count: int


class RootCauseRequest(BaseModel):
    incident_id: int | None = None
    description: str | None = None


class RootCauseResponse(BaseModel):
    available: bool
    root_cause: str
    confidence: str
    recommendation: str
    evidence: list[str]
    incident_id: int | None = None


class IncidentSummaryRequest(BaseModel):
    incident_id: int


class IncidentSummaryResponse(BaseModel):
    available: bool
    summary: str


class RecommendationsResponse(BaseModel):
    available: bool
    recommendations: str


class QueryRequest(BaseModel):
    question: str


class QueryResponse(BaseModel):
    available: bool
    answer: str


class ChatMessage(BaseModel):
    role: str
    message: str
    created_at: str
