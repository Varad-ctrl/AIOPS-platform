import Gauge from "@/components/Gauge";
import StatCard from "@/components/StatCard";
import StatusBadge from "@/components/StatusBadge";
import { usePolling } from "@/hooks/usePolling";
import { fetchAllCoreMetrics } from "@/services/metricsService";
import { fetchClusterHealth } from "@/services/kubernetesService";

export default function Infrastructure() {
  const { data: metrics } = usePolling(fetchAllCoreMetrics, 15000);
  const { data: cluster } = usePolling(fetchClusterHealth, 20000);

  return (
    <div className="space-y-6">
      <div>
        <p className="label-eyebrow">Infrastructure</p>
        <h1 className="text-xl font-semibold text-ink-primary mt-1">System overview</h1>
        <p className="text-sm text-ink-secondary mt-1">
          Node-level resource usage plus a rollup of cluster health.
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

      <div className="panel p-6">
        <div className="flex items-center justify-between mb-4">
          <p className="label-eyebrow">Cluster</p>
          {cluster && <StatusBadge status={cluster.cluster} />}
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
          <StatCard label="Nodes" value={String(cluster?.nodes ?? "—")} tone="info" />
          <StatCard label="Pods" value={String(cluster?.pods ?? "—")} tone="info" />
          <StatCard label="Deployments" value={String(cluster?.deployments ?? "—")} tone="info" />
        </div>
        {cluster?.cluster === "Disconnected" && (
          <p className="text-xs text-ink-muted mt-4">
            No Kubernetes cluster connected. Point the backend at a kubeconfig or run it in-cluster
            to populate this section.
          </p>
        )}
      </div>
    </div>
  );
}
