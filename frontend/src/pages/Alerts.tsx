import { useState } from "react";
import StatCard from "@/components/StatCard";
import StatusBadge from "@/components/StatusBadge";
import { useAuth } from "@/contexts/AuthContext";
import { usePolling } from "@/hooks/usePolling";
import {
  acknowledgeAlert,
  fetchActiveAlerts,
  fetchAlertDashboard,
  fetchAllAlerts,
  resolveAlert,
} from "@/services/alertsService";

const STATUS_BADGE: Record<string, string> = {
  active: "Failed",
  acknowledged: "Pending",
  resolved: "Healthy",
};

export default function Alerts() {
  const [showAll, setShowAll] = useState(false);
  const [busyId, setBusyId] = useState<number | null>(null);
  const { user } = useAuth();
  const canManage = user?.role === "admin" || user?.role === "devops_engineer";

  const { data: active, error: activeError, isLoading } = usePolling(fetchActiveAlerts, 15000);
  const { data: all } = usePolling(fetchAllAlerts, 15000);
  const { data: summary } = usePolling(fetchAlertDashboard, 15000);

  const alerts = showAll ? all : active;

  async function handleAcknowledge(id: number) {
    setBusyId(id);
    try {
      await acknowledgeAlert(id);
    } finally {
      setBusyId(null);
    }
  }

  async function handleResolve(id: number) {
    setBusyId(id);
    try {
      await resolveAlert(id);
    } finally {
      setBusyId(null);
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <p className="label-eyebrow">Alerting</p>
          <h1 className="text-xl font-semibold text-ink-primary mt-1">Alerts</h1>
          <p className="text-sm text-ink-secondary mt-1">
            {showAll ? "Full alert history." : "Currently open alerts (active or acknowledged)."}
          </p>
        </div>
        <button onClick={() => setShowAll((v) => !v)} className="btn-ghost text-xs">
          {showAll ? "Show active only" : "Show all history"}
        </button>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <StatCard
          label="Active"
          value={String(summary?.active_alerts ?? "—")}
          tone={summary && summary.active_alerts > 0 ? "crit" : "ok"}
        />
        <StatCard label="Critical" value={String(summary?.critical ?? "—")} tone="crit" />
        <StatCard label="Warning" value={String(summary?.warning ?? "—")} tone="warn" />
        <StatCard label="Resolved today" value={String(summary?.resolved_today ?? "—")} tone="ok" />
      </div>

      <div className="panel divide-y divide-base-700">
        {(alerts ?? []).map((alert) => (
          <div key={alert.id} className="p-4 flex items-start justify-between gap-4">
            <div className="min-w-0">
              <div className="flex items-center gap-2 mb-1 flex-wrap">
                <StatusBadge status={STATUS_BADGE[alert.status] ?? "Unknown"} />
                <span className="text-xs font-mono text-ink-muted uppercase">{alert.status}</span>
                <span className="text-xs font-mono text-ink-muted uppercase">· {alert.source}</span>
              </div>
              <p className="text-sm font-medium text-ink-primary">{alert.title}</p>
              <p className="text-xs text-ink-secondary mt-1">{alert.description}</p>
              {alert.acknowledged_by && (
                <p className="text-xs text-ink-muted mt-1">Acknowledged by {alert.acknowledged_by}</p>
              )}
            </div>

            {canManage && alert.status !== "resolved" && (
              <div className="flex gap-2 shrink-0">
                {alert.status === "active" && (
                  <button
                    onClick={() => handleAcknowledge(alert.id)}
                    disabled={busyId === alert.id}
                    className="btn-ghost text-xs py-1"
                  >
                    Acknowledge
                  </button>
                )}
                <button
                  onClick={() => handleResolve(alert.id)}
                  disabled={busyId === alert.id}
                  className="btn-primary text-xs py-1"
                >
                  Resolve
                </button>
              </div>
            )}
          </div>
        ))}
        {!isLoading && (alerts ?? []).length === 0 && !activeError && (
          <div className="p-8 text-center text-sm text-ink-muted">
            {showAll ? "No alerts have fired yet." : "No open alerts — all clear."}
          </div>
        )}
      </div>
    </div>
  );
}
