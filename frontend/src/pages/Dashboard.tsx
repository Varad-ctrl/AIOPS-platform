import { useAuth } from "@/contexts/AuthContext";
import StatCard from "@/components/StatCard";
import Gauge from "@/components/Gauge";
import { usePolling } from "@/hooks/usePolling";
import { fetchAllCoreMetrics } from "@/services/metricsService";
import { fetchActiveAlerts } from "@/services/alertsService";
import { fetchClusterHealth } from "@/services/kubernetesService";

export default function Dashboard() {
  const { user } = useAuth();
  const { data: metrics } = usePolling(fetchAllCoreMetrics, 15000);
  const { data: activeAlerts } = usePolling(fetchActiveAlerts, 15000);
  const { data: cluster } = usePolling(fetchClusterHealth, 20000);

  return (
    <div className="space-y-6">
      <div>
        <p className="label-eyebrow">Overview</p>
        <h1 className="text-xl font-semibold text-ink-primary mt-1">
          Welcome back, {user?.full_name || user?.email}
        </h1>
        <p className="text-sm text-ink-secondary mt-1">
          Live infrastructure metrics, cluster health, and alerts at a glance.
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

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <StatCard
          label="Active alerts"
          value={String(activeAlerts?.length ?? 0)}
          tone={activeAlerts && activeAlerts.length > 0 ? "crit" : "ok"}
        />
        <StatCard
          label="Cluster nodes"
          value={String(cluster?.nodes ?? "—")}
          tone="info"
          hint={cluster?.cluster}
        />
        <StatCard label="Your role" value={user?.role ?? "—"} tone="info" />
      </div>

      <div className="panel p-6">
        <p className="label-eyebrow mb-3">Roadmap status</p>
        <ul className="space-y-2 text-sm">
          <RoadmapRow label="Phase 1 — Project Foundation" status="done" />
          <RoadmapRow label="Phase 2 — Observability Layer" status="done" />
          <RoadmapRow label="Phase 3 — Log Intelligence" status="pending" />
          <RoadmapRow label="Phase 4 — AI Agent" status="pending" />
          <RoadmapRow label="Phase 5 — Incident Detection Engine" status="pending" />
          <RoadmapRow label="Phase 6 — AI Root Cause Analysis" status="pending" />
          <RoadmapRow label="Phase 7 — Notification & Alerting" status="pending" />
        </ul>
      </div>
    </div>
  );
}

function RoadmapRow({ label, status }: { label: string; status: "done" | "pending" }) {
  return (
    <li className="flex items-center justify-between border-b border-base-700 last:border-0 py-2">
      <span className="text-ink-secondary">{label}</span>
      <span
        className={`text-xs font-mono uppercase tracking-wide ${
          status === "done" ? "text-signal-ok" : "text-ink-muted"
        }`}
      >
        {status === "done" ? "complete" : "not started"}
      </span>
    </li>
  );
}
