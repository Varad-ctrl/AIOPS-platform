from pydantic import BaseModel


class LogEntry(BaseModel):
    timestamp: str
    message: str
    labels: dict[str, str]


class LogSearchResponse(BaseModel):
    available: bool
    count: int
    items: list[LogEntry]
