import { Link } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import StatCard from "@/components/StatCard";
import Gauge from "@/components/Gauge";
import { usePolling } from "@/hooks/usePolling";
import { fetchAllCoreMetrics } from "@/services/metricsService";
import { fetchActiveAlerts } from "@/services/alertsService";
import { fetchClusterHealth } from "@/services/kubernetesService";
import { fetchIncidents } from "@/services/incidentsService";
import { fetchRecentLogs } from "@/services/logsService";

export default function Dashboard() {
  const { user } = useAuth();
  const { data: metrics } = usePolling(fetchAllCoreMetrics, 15000);
  const { data: activeAlerts } = usePolling(fetchActiveAlerts, 15000);
  const { data: cluster } = usePolling(fetchClusterHealth, 20000);
  const { data: openIncidents } = usePolling(() => fetchIncidents("open"), 20000);
  const { data: recentLogs } = usePolling(() => fetchRecentLogs(1, 8), 20000);

  return (
    <div className="space-y-6">
      <div>
        <p className="label-eyebrow">Unified overview</p>
        <h1 className="text-xl font-semibold text-ink-primary mt-1">
          Welcome back, {user?.full_name || user?.email}
        </h1>
        <p className="text-sm text-ink-secondary mt-1">
          Metrics, cluster health, alerts, incidents, and logs — one screen, everything the AI
          agent reasons over.
        </p>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <Gauge label="CPU" value={metrics?.cpu.value ?? null} available={metrics?.cpu.available} />
        <Gauge
          label="Memory"
          value={metrics?.memory.value ?? null}
          available={metrics?.memory.available}
        />
        <Gauge
          label="Disk"
          value={metrics?.disk.value ?? null}
          available={metrics?.disk.available}
        />
        <Gauge
          label="Network"
          value={metrics?.network.value ?? null}
          unit="B/s"
          available={metrics?.network.available}
        />
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <StatCard
          label="Active alerts"
          value={String(activeAlerts?.length ?? 0)}
          tone={activeAlerts && activeAlerts.length > 0 ? "crit" : "ok"}
        />
        <StatCard
          label="Open incidents"
          value={String(openIncidents?.length ?? 0)}
          tone={openIncidents && openIncidents.length > 0 ? "warn" : "ok"}
        />
        <StatCard
          label="Cluster nodes"
          value={String(cluster?.nodes ?? "—")}
          tone="info"
          hint={cluster?.cluster}
        />
        <StatCard label="Your role" value={user?.role ?? "—"} tone="info" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="panel">
          <div className="px-4 py-3 border-b border-base-700 flex items-center justify-between">
            <p className="label-eyebrow">Recent logs</p>
            <Link to="/logs" className="text-xs text-accent hover:underline">
              Open Logs →
            </Link>
          </div>
          <div className="max-h-64 overflow-y-auto font-mono text-xs">
            {(recentLogs?.items ?? []).map((entry, i) => (
              <div key={i} className="px-4 py-2 border-b border-base-700 last:border-0 flex gap-2">
                <span className="text-ink-muted whitespace-nowrap">
                  {new Date(entry.timestamp).toLocaleTimeString()}
                </span>
                <span className="text-ink-secondary truncate">{entry.message}</span>
              </div>
            ))}
            {(recentLogs?.items ?? []).length === 0 && (
              <div className="p-6 text-center text-xs text-ink-muted">
                {recentLogs?.available === false
                  ? "Connect Loki + Promtail to see logs here."
                  : "No recent log lines."}
              </div>
            )}
          </div>
        </div>

        <div className="panel p-4 flex flex-col">
          <p className="label-eyebrow mb-2">Ask the AI agent</p>
          <p className="text-sm text-ink-secondary mb-4">
            "Why is CPU high?" · "Show critical errors in the last hour" · "Which service errored
            most today?"
          </p>
          <Link to="/chat" className="btn-primary text-sm mt-auto self-start">
            Open AI Chat
          </Link>
        </div>
      </div>

      <div className="panel p-6">
        <p className="label-eyebrow mb-3">Grafana dashboards</p>
        <p className="text-sm text-ink-secondary mb-3">
          Cluster, Node, Pod, Alert, Incident, and Jenkins dashboards are provisioned automatically.
        </p>
        <a
          href="http://localhost:3001"
          target="_blank"
          rel="noreferrer"
          className="btn-ghost text-xs inline-flex"
        >
          Open Grafana →
        </a>
      </div>
    </div>
  );
}


