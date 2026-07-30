"""
Module 3.3/5.2 (AI log analysis + AI service orchestration) and 3.4/5.4
(natural language queries + full context engine).

Builds on the lower-level services rather than duplicating their logic:
    - LokiService        -> log lines
    - PrometheusService  -> current metric values
    - KubernetesService   -> cluster/pod/node summary  (Module 5.4)
    - JenkinsService       -> job/build status           (Module 5.4)
    - AlertService          -> active alerts (Module 2.6)
    - IncidentService        -> open incidents (Module 2.6.5)
    - AIService                -> the actual LLM call (ai_service.py)

Every public method degrades gracefully: if the AI backend isn't
configured, callers get a clear `available: False` result instead of a
500 - consistent with how every other integration in this project behaves
when its upstream isn't reachable.

Conversation history and RCA outputs are persisted to the `chat_history`
and `analysis_logs` tables (both created in Phase 1, unused until Phase 3).
"""
import json

from sqlalchemy.orm import Session

from app.core.logging_config import get_logger
from app.models.operations import AnalysisLog, ChatHistory, Incident
from app.services.ai_service import AIService
from app.services.alert_service import AlertService
from app.services.incident_service import IncidentNotFoundError, IncidentService
from app.services.jenkins_service import JenkinsService
from app.services.kubernetes_service import KubernetesService
from app.services.loki_service import LokiService
from app.services.prometheus_service import PrometheusService

logger = get_logger("insight_service")

LOG_SUMMARY_SYSTEM_PROMPT = (
    "You are an SRE assistant summarizing raw log output for a DevOps engineer. "
    "Be concise and factual. Group related lines, call out anything that looks "
    "like an error or warning, and never invent details that aren't in the logs. "
    "If the logs look completely normal, say so plainly."
)

ANOMALY_SYSTEM_PROMPT = (
    "You are an SRE assistant looking for anomalies in log output: repeated "
    "errors, sudden bursts of a particular message, stack traces, timeouts, "
    "or anything that deviates from normal operation. List what you find as "
    "short bullet points. If nothing anomalous stands out, say so plainly - "
    "do not manufacture findings."
)

ROOT_CAUSE_SYSTEM_PROMPT = (
    "You are an SRE assistant performing root cause analysis. You will be "
    "given a description of a problem plus related pod/cluster state, logs, "
    "metrics, and active alerts. Respond ONLY with a JSON object with these "
    "exact keys: \"root_cause\" (string), \"confidence\" (one of \"low\", "
    "\"medium\", \"high\"), \"recommendation\" (string, a concrete next "
    "action), \"evidence\" (array of short strings, each citing a specific "
    "fact from the provided context). Base every claim only on the provided "
    "context - if the evidence is insufficient to be confident, say so in "
    "root_cause and set confidence to \"low\" rather than guessing."
)

INCIDENT_SUMMARY_SYSTEM_PROMPT = (
    "You are an SRE assistant. Summarize the given incident in 2-3 sentences "
    "for a status update to other engineers: what's affected, current "
    "severity/status, and any notable evidence. Be factual and concise."
)

RECOMMENDATIONS_SYSTEM_PROMPT = (
    "You are an SRE assistant. Given the current alerts, incidents, and "
    "metrics, suggest concrete remediation actions (e.g. restart a "
    "deployment, scale up, increase memory limits, roll back). Return a "
    "short bullet list, most urgent first. If nothing needs action, say so "
    "plainly rather than inventing busywork."
)

QUERY_SYSTEM_PROMPT = (
    "You are an AIOps assistant embedded in a monitoring dashboard. Answer "
    "the engineer's question using only the context provided below (current "
    "metrics, cluster state, Jenkins status, active alerts, open incidents, "
    "and a sample of recent logs). Be direct and specific. If the context "
    "doesn't contain enough information to answer confidently, say what's "
    "missing rather than speculating."
)

UNAVAILABLE_MESSAGE = (
    "AI analysis is not available - set LLM_API_KEY (or OPENAI_API_KEY) for "
    "your chosen LLM_PROVIDER (groq | openai | ollama) in your environment "
    "to enable it."
)


class InsightService:
    def __init__(self, db: Session):
        self.db = db
        self.ai = AIService()
        self.loki = LokiService()
        self.prometheus = PrometheusService()
        self.kubernetes = KubernetesService()
        self.jenkins = JenkinsService()
        self.alerts = AlertService(db)
        self.incidents = IncidentService(db)

    @property
    def ai_configured(self) -> bool:
        return self.ai.configured

    # --- Module 3.3 / 5.3: AI Log Analysis --------------------------------

    async def summarize_logs(
        self,
        *,
        namespace: str | None = None,
        pod: str | None = None,
        hours: int = 1,
    ) -> dict:
        logs = await self.loki.search(
            namespace=namespace,
            pod=pod,
            hours=hours,
            limit=50,
        )

        if not self.ai.configured:
            return {
                "available": False,
                "summary": UNAVAILABLE_MESSAGE,
                "log_count": len(logs),
            }

        if not logs:
            return {
                "available": True,
                "summary": "No log lines found for that window.",
                "log_count": 0,
            }

        # Keep only the latest 30 logs
        logs = logs[-30:]

        # Convert logs into text
        log_text = _format_logs(logs)

        # Prevent oversized prompts
        MAX_PROMPT_CHARS = 12000

        if len(log_text) > MAX_PROMPT_CHARS:
            log_text = log_text[:MAX_PROMPT_CHARS]

        print(f"Prompt size: {len(log_text)} characters")

        summary = await self.ai.complete(
            LOG_SUMMARY_SYSTEM_PROMPT,
            log_text,
        )

        return {
            "available": summary is not None,
            "summary": summary or UNAVAILABLE_MESSAGE,
            "log_count": len(logs),
        }

    async def detect_anomalies(
        self,
        *,
        namespace: str | None = None,
        pod: str | None = None,
        hours: int = 1,
    ) -> dict:

     logs = await self.loki.search(
        namespace=namespace,
        pod=pod,
        hours=hours,
        limit=50,
    )

     if not self.ai.configured:
        return {
            "available": False,
            "findings": UNAVAILABLE_MESSAGE,
            "log_count": len(logs),
        }

     if not logs:
        return {
            "available": True,
            "findings": "No logs to analyze in that window.",
            "log_count": 0,
        }

    # Keep only the latest 30 logs
     logs = logs[-30:]

    # Convert logs into text
     log_text = _format_logs(logs)

    # Prevent oversized prompts
     MAX_PROMPT_CHARS = 12000

     if len(log_text) > MAX_PROMPT_CHARS:
        log_text = log_text[:MAX_PROMPT_CHARS]

     print(f"Prompt size: {len(log_text)} characters")

     findings = await self.ai.complete(
        ANOMALY_SYSTEM_PROMPT,
        log_text,
     )

     return {
            "available": findings is not None,
            "findings": findings or UNAVAILABLE_MESSAGE,
            "log_count": len(logs),
        }

    async def log_analysis(
        self, *, namespace: str | None = None, pod: str | None = None, hours: int = 1
    ) -> dict:
        """Module 5.3 POST /ai/log-analysis - summary + anomalies in one call."""
        summary = await self.summarize_logs(namespace=namespace, pod=pod, hours=hours)
        anomalies = await self.detect_anomalies(namespace=namespace, pod=pod, hours=hours)
        return {
            "available": summary["available"] and anomalies["available"],
            "summary": summary["summary"],
            "findings": anomalies["findings"],
            "log_count": summary["log_count"],
        }

    # --- Module 5.6: Root Cause Analysis ------------------------------------

    async def root_cause_analysis(
        self, *, incident_id: int | None = None, description: str | None = None
    ) -> dict:
        """
        Structured RCA workflow:
            collect pod/cluster state + logs + metrics + active alerts -> LLM
            -> {root_cause, confidence, recommendation, evidence}

        Can be driven by an existing incident (`incident_id`) or a freeform
        description (e.g. "why is nginx restarting?") for cases where no
        incident has been opened yet.
        """
        incident: Incident | None = None
        if incident_id is not None:
            try:
                incident = self.incidents.get_incident(incident_id)
            except IncidentNotFoundError:
                return {
                    "available": False,
                    "root_cause": f"Incident {incident_id} not found.",
                    "confidence": "low",
                    "recommendation": "",
                    "evidence": [],
                    "incident_id": incident_id,
                }

        search_term = incident.title if incident else (description or "")
        logs = await self.loki.search(search=search_term, hours=6, limit=100) if search_term else []
        if not logs:
            logs = await self.loki.recent(limit=50, hours=1)

        cpu = await self.prometheus.get_metric("cpu")
        memory = await self.prometheus.get_metric("memory")
        disk = await self.prometheus.get_metric("disk")
        cluster = self.kubernetes.cluster_summary()
        active_alerts = self.alerts.list_alerts(active_only=True)

        context = (
            f"Problem: {incident.title if incident else description}\n"
            f"Severity: {incident.severity if incident else 'unknown'}\n"
            f"Description: {incident.description if incident else ''}\n\n"
            f"Cluster: {cluster.get('cluster')}, nodes={cluster.get('nodes')}, "
            f"pods={cluster.get('pods')}, deployments={cluster.get('deployments')}\n\n"
            f"Current metrics: cpu={cpu['value']}{cpu['unit'] if cpu['available'] else ' (unavailable)'}, "
            f"memory={memory['value']}{memory['unit'] if memory['available'] else ' (unavailable)'}, "
            f"disk={disk['value']}{disk['unit'] if disk['available'] else ' (unavailable)'}\n\n"
            f"Active alerts:\n"
            + ("\n".join(f"- [{a.severity}] {a.title}" for a in active_alerts) or "None")
            + f"\n\nRelated logs:\n{_format_logs(logs)}"
        )

        if not self.ai.configured:
            return {
                "available": False,
                "root_cause": UNAVAILABLE_MESSAGE,
                "confidence": "low",
                "recommendation": "",
                "evidence": [],
                "incident_id": incident_id,
            }

        raw = await self.ai.complete(ROOT_CAUSE_SYSTEM_PROMPT, context, json_mode=True)
        parsed = _parse_rca_json(raw)

        if parsed and incident_id is not None:
            self.db.add(
                AnalysisLog(
                    incident_id=incident_id,
                    summary=parsed["root_cause"][:2000],
                    root_cause=parsed["root_cause"],
                    recommended_fix=parsed["recommendation"],
                )
            )
            self.db.commit()

        if not parsed:
            return {
                "available": False,
                "root_cause": raw or UNAVAILABLE_MESSAGE,
                "confidence": "low",
                "recommendation": "",
                "evidence": [],
                "incident_id": incident_id,
            }

        return {"available": True, "incident_id": incident_id, **parsed}

    async def incident_summary(self, incident_id: int) -> dict:
        """Module 5.3 POST /ai/incident-summary"""
        try:
            incident = self.incidents.get_incident(incident_id)
        except IncidentNotFoundError:
            return {"available": False, "summary": f"Incident {incident_id} not found."}

        if not self.ai.configured:
            return {"available": False, "summary": UNAVAILABLE_MESSAGE}

        context = (
            f"Title: {incident.title}\nSeverity: {incident.severity}\n"
            f"Status: {incident.status}\nDescription: {incident.description}"
        )
        summary = await self.ai.complete(INCIDENT_SUMMARY_SYSTEM_PROMPT, context)
        return {"available": summary is not None, "summary": summary or UNAVAILABLE_MESSAGE}

    async def recommendations(self) -> dict:
        """Module 5.3 POST /ai/recommendations"""
        if not self.ai.configured:
            return {"available": False, "recommendations": UNAVAILABLE_MESSAGE}

        context = await self._assemble_context(include_logs=False)
        result = await self.ai.complete(RECOMMENDATIONS_SYSTEM_PROMPT, context)
        return {"available": result is not None, "recommendations": result or UNAVAILABLE_MESSAGE}

    # --- Module 3.4 / 5.3 / 5.5: Natural Language Queries / Chat ------------

    async def answer_query(self, question: str, user_id: int) -> dict:
        """Answers a free-form question by assembling live context (metrics,
        cluster, Jenkins, active alerts, open incidents, recent error logs)
        and asking the AI. Persists both sides to chat_history."""
        self.db.add(ChatHistory(user_id=user_id, role="user", message=question))
        self.db.commit()

        if not self.ai.configured:
            answer = UNAVAILABLE_MESSAGE
            self.db.add(ChatHistory(user_id=user_id, role="assistant", message=answer))
            self.db.commit()
            return {"available": False, "answer": answer}

        context = await self._assemble_context()
        prompt = f"Question: {question}\n\nContext:\n{context}"
        answer = await self.ai.complete(QUERY_SYSTEM_PROMPT, prompt)
        answer = answer or UNAVAILABLE_MESSAGE

        self.db.add(ChatHistory(user_id=user_id, role="assistant", message=answer))
        self.db.commit()

        return {"available": answer != UNAVAILABLE_MESSAGE, "answer": answer}

    def get_chat_history(self, user_id: int, limit: int = 50) -> list[ChatHistory]:
        return (
            self.db.query(ChatHistory)
            .filter(ChatHistory.user_id == user_id)
            .order_by(ChatHistory.created_at.desc())
            .limit(limit)
            .all()[::-1]
        )

    async def _assemble_context(self, include_logs: bool = True) -> str:
        cpu = await self.prometheus.get_metric("cpu")
        memory = await self.prometheus.get_metric("memory")
        disk = await self.prometheus.get_metric("disk")
        cluster = self.kubernetes.cluster_summary()
        jenkins_jobs = await self.jenkins.get_jobs() if self.jenkins.configured else []
        active_alerts = self.alerts.list_alerts(active_only=True)
        open_incidents = self.incidents.list_incidents(status="open")

        alerts_text = (
            "\n".join(f"- [{a.severity}] {a.title}: {a.description}" for a in active_alerts)
            or "None"
        )
        incidents_text = (
            "\n".join(f"- [{i.severity}] {i.title} (status: {i.status})" for i in open_incidents)
            or "None"
        )
        jenkins_text = (
            "\n".join(f"- {j['name']}: {j['status']}" for j in jenkins_jobs)
            or ("Not configured" if not self.jenkins.configured else "No jobs")
        )

        context = (
            f"Metrics: cpu={cpu['value']}%, memory={memory['value']}%, disk={disk['value']}%\n\n"
            f"Cluster: {cluster.get('cluster')}, nodes={cluster.get('nodes')}, "
            f"pods={cluster.get('pods')}, deployments={cluster.get('deployments')}\n\n"
            f"Jenkins jobs:\n{jenkins_text}\n\n"
            f"Active alerts:\n{alerts_text}\n\n"
            f"Open incidents:\n{incidents_text}"
        )

        if include_logs:
            recent_errors = await self.loki.errors_only(hours=1, limit=20)
            context += f"\n\nRecent error logs:\n{_format_logs(recent_errors) or 'None'}"

        return context


def _format_logs(logs: list[dict], max_lines: int = 200) -> str:
    lines = []
    for entry in logs[:max_lines]:
        labels = entry.get("labels", {})
        source = labels.get("container") or labels.get("service") or labels.get("pod") or "unknown"
        lines.append(f"[{entry['timestamp']}] ({source}) {entry['message']}")
    return "\n".join(lines)


def _parse_rca_json(raw: str | None) -> dict | None:
    """Parses the structured RCA response, tolerating minor formatting
    issues (e.g. a model wrapping JSON in markdown fences despite instructions)."""
    if not raw:
        return None
    text = raw.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.startswith("json"):
            text = text[4:]
    try:
        data = json.loads(text)
        return {
            "root_cause": str(data.get("root_cause", "")),
            "confidence": str(data.get("confidence", "low")),
            "recommendation": str(data.get("recommendation", "")),
            "evidence": [str(e) for e in data.get("evidence", [])],
        }
    except (json.JSONDecodeError, AttributeError):
        logger.warning("rca_json_parse_failed", raw_preview=text[:200])
        return None
