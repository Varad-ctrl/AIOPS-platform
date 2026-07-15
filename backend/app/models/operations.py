"""
Operational tables scaffolded in Phase 1 (Module 4.3) so migrations and the
schema are ready ahead of Phases 2-9, where they get populated:

- chat_history      -> Phase 4 (AI Agent)
- alerts            -> Phase 5 (Incident Detection Engine)
- incidents         -> Phase 5 / Phase 6 (RCA)
- analysis_logs     -> Phase 6 (AI Root Cause Analysis)
- notification_logs -> Phase 7 (Notification & Alerting)
- audit_logs        -> cross-cutting security/audit trail
"""
from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base_class import Base


class ChatHistory(Base):
    __tablename__ = "chat_history"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False)  # user | assistant
    message: Mapped[str] = mapped_column(Text, nullable=False)


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    source: Mapped[str] = mapped_column(String(100), nullable=False)  # prometheus, k8s, jenkins...
    severity: Mapped[str] = mapped_column(String(20), nullable=False, default="low")
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")
    # "active" -> "acknowledged" -> "resolved". `resolved` is kept as a
    # denormalized bool (status == "resolved") so existing queries/filters
    # that only care about open-vs-closed don't need to change.
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")
    resolved: Mapped[bool] = mapped_column(default=False)
    acknowledged_by: Mapped[str] = mapped_column(String(255), nullable=False, default="")


class Incident(Base):
    __tablename__ = "incidents"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    alert_id: Mapped[int | None] = mapped_column(ForeignKey("alerts.id"), nullable=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False, default="low")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="open")
    description: Mapped[str] = mapped_column(Text, default="")


class AnalysisLog(Base):
    __tablename__ = "analysis_logs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    incident_id: Mapped[int] = mapped_column(ForeignKey("incidents.id"), nullable=True)
    summary: Mapped[str] = mapped_column(Text, default="")
    root_cause: Mapped[str] = mapped_column(Text, default="")
    recommended_fix: Mapped[str] = mapped_column(Text, default="")


class NotificationLog(Base):
    __tablename__ = "notification_logs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    channel: Mapped[str] = mapped_column(String(50), nullable=False, default="email")
    recipient: Mapped[str] = mapped_column(String(255), nullable=False)
    subject: Mapped[str] = mapped_column(String(255), default="")
    status: Mapped[str] = mapped_column(String(20), default="sent")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=True)
    action: Mapped[str] = mapped_column(String(255), nullable=False)
    detail: Mapped[str] = mapped_column(Text, default="")
    ip_address: Mapped[str] = mapped_column(String(64), default="")
