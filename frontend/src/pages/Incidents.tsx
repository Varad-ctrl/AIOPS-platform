import { useState } from "react";
import StatusBadge from "@/components/StatusBadge";
import { useAuth } from "@/contexts/AuthContext";
import { usePolling } from "@/hooks/usePolling";
import { fetchIncidents, updateIncidentStatus, type Incident } from "@/services/incidentsService";
import { incidentSummary, rootCauseForIncident } from "@/services/aiService";
import type { IncidentSummaryResult, RootCauseResult } from "@/types";

const STATUS_BADGE: Record<string, string> = {
  open: "Failed",
  acknowledged: "Pending",
  resolved: "Healthy",
};

const CONFIDENCE_TONE: Record<string, string> = {
  high: "text-signal-ok",
  medium: "text-signal-warn",
  low: "text-signal-crit",
};

export default function Incidents() {
  const { user } = useAuth();
  const canManage = user?.role === "admin" || user?.role === "devops_engineer";
  const [busyId, setBusyId] = useState<number | null>(null);
  const [rca, setRca] = useState<Record<number, RootCauseResult>>({});
  const [summaries, setSummaries] = useState<Record<number, IncidentSummaryResult>>({});
  const [loadingId, setLoadingId] = useState<number | null>(null);

  const { data: incidents } = usePolling(() => fetchIncidents(), 15000);

  async function handleStatusChange(incident: Incident, status: string) {
    setBusyId(incident.id);
    try {
      await updateIncidentStatus(incident.id, status);
    } finally {
      setBusyId(null);
    }
  }

  async function handleRCA(incident: Incident) {
    setLoadingId(incident.id);
    try {
      const result = await rootCauseForIncident(incident.id);
      setRca((prev) => ({ ...prev, [incident.id]: result }));
    } finally {
      setLoadingId(null);
    }
  }

  async function handleSummary(incident: Incident) {
    setLoadingId(incident.id);
    try {
      const result = await incidentSummary(incident.id);
      setSummaries((prev) => ({ ...prev, [incident.id]: result }));
    } finally {
      setLoadingId(null);
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <p className="label-eyebrow">Incident management</p>
        <h1 className="text-xl font-semibold text-ink-primary mt-1">Incidents</h1>
        <p className="text-sm text-ink-secondary mt-1">
          Tracked incidents, promoted from alerts or opened directly, with AI-assisted root cause
          analysis.
        </p>
      </div>

      <div className="panel divide-y divide-base-700">
        {(incidents ?? []).map((incident) => (
          <div key={incident.id} className="p-4 space-y-3">
            <div className="flex items-start justify-between gap-4 flex-wrap">
              <div>
                <div className="flex items-center gap-2 mb-1">
                  <StatusBadge status={STATUS_BADGE[incident.status] ?? "Unknown"} />
                  <span className="text-xs font-mono text-ink-muted uppercase">
                    {incident.status}
                  </span>
                  <span className="text-xs font-mono text-ink-muted uppercase">
                    · {incident.severity}
                  </span>
                  {incident.alert_id && (
                    <span className="text-xs font-mono text-ink-muted">
                      from alert #{incident.alert_id}
                    </span>
                  )}
                </div>
                <p className="text-sm font-medium text-ink-primary">{incident.title}</p>
                {incident.description && (
                  <p className="text-xs text-ink-secondary mt-1">{incident.description}</p>
                )}
              </div>

              <div className="flex gap-2 shrink-0">
                <button
                  onClick={() => handleSummary(incident)}
                  disabled={loadingId === incident.id}
                  className="btn-ghost text-xs py-1"
                >
                  {loadingId === incident.id ? "…" : "AI: Summarize"}
                </button>
                <button
                  onClick={() => handleRCA(incident)}
                  disabled={loadingId === incident.id}
                  className="btn-ghost text-xs py-1"
                >
                  {loadingId === incident.id ? "Analyzing…" : "AI: Root cause"}
                </button>
                {canManage && incident.status === "open" && (
                  <button
                    onClick={() => handleStatusChange(incident, "acknowledged")}
                    disabled={busyId === incident.id}
                    className="btn-ghost text-xs py-1"
                  >
                    Acknowledge
                  </button>
                )}
                {canManage && incident.status !== "resolved" && (
                  <button
                    onClick={() => handleStatusChange(incident, "resolved")}
                    disabled={busyId === incident.id}
                    className="btn-primary text-xs py-1"
                  >
                    Resolve
                  </button>
                )}
              </div>
            </div>

            {summaries[incident.id] && (
              <div className="bg-base-800 border border-base-600 rounded p-3 text-xs text-ink-secondary">
                {summaries[incident.id].summary}
              </div>
            )}

            {rca[incident.id] && (
              <div className="bg-base-800 border border-base-600 rounded p-3 text-xs space-y-2">
                <div className="flex items-center gap-2">
                  <span className="label-eyebrow">Root cause</span>
                  <span
                    className={`font-mono uppercase ${
                      CONFIDENCE_TONE[rca[incident.id].confidence] ?? "text-ink-muted"
                    }`}
                  >
                    {rca[incident.id].confidence} confidence
                  </span>
                </div>
                <p className="text-ink-secondary">{rca[incident.id].root_cause}</p>
                {rca[incident.id].recommendation && (
                  <>
                    <p className="label-eyebrow">Recommendation</p>
                    <p className="text-ink-secondary">{rca[incident.id].recommendation}</p>
                  </>
                )}
                {rca[incident.id].evidence.length > 0 && (
                  <>
                    <p className="label-eyebrow">Evidence</p>
                    <ul className="list-disc pl-4 text-ink-secondary space-y-0.5">
                      {rca[incident.id].evidence.map((e, i) => (
                        <li key={i}>{e}</li>
                      ))}
                    </ul>
                  </>
                )}
              </div>
            )}
          </div>
        ))}
        {(incidents ?? []).length === 0 && (
          <div className="p-8 text-center text-sm text-ink-muted">
            No incidents yet. Promote an active alert to an incident from the Alerts page, or
            create one directly via the API.
          </div>
        )}
      </div>
    </div>
  );
}
