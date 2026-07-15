import Gauge from "@/components/Gauge";
import HistoryChart from "@/components/HistoryChart";
import { usePolling } from "@/hooks/usePolling";
import { fetchAllCoreMetrics, fetchMetricHistory } from "@/services/metricsService";

export default function Metrics() {
  const { data: metrics } = usePolling(fetchAllCoreMetrics, 15000);
  const { data: cpuHistory } = usePolling(() => fetchMetricHistory("cpu", 24), 60000);
  const { data: memoryHistory } = usePolling(() => fetchMetricHistory("memory", 24), 60000);
  const { data: diskHistory } = usePolling(() => fetchMetricHistory("disk", 24), 60000);
  const { data: networkHistory } = usePolling(() => fetchMetricHistory("network", 24), 60000);

  return (
    <div className="space-y-6">
      <div>
        <p className="label-eyebrow">Observability</p>
        <h1 className="text-xl font-semibold text-ink-primary mt-1">Metrics</h1>
        <p className="text-sm text-ink-secondary mt-1">
          Live infrastructure metrics from Prometheus, refreshed every 15 seconds.
        </p>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <Gauge
          label="CPU"
          value={metrics?.cpu.value ?? null}
          available={metrics?.cpu.available ?? false}
        />
        <Gauge
          label="Memory"
          value={metrics?.memory.value ?? null}
          available={metrics?.memory.available ?? false}
        />
        <Gauge
          label="Disk"
          value={metrics?.disk.value ?? null}
          available={metrics?.disk.available ?? false}
        />
        <Gauge
          label="Network"
          value={metrics?.network.value ?? null}
          unit="B/s"
          available={metrics?.network.available ?? false}
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <HistoryChart title="CPU history (24h)" data={cpuHistory ?? []} color="#4C8BF5" />
        <HistoryChart title="Memory history (24h)" data={memoryHistory ?? []} color="#5EEAD4" />
        <HistoryChart title="Disk history (24h)" data={diskHistory ?? []} color="#E2574C" />
        <HistoryChart
          title="Network history (24h)"
          data={networkHistory ?? []}
          color="#E0A526"
          unit="B/s"
        />
      </div>

      {!metrics?.cpu.available && (
        <p className="text-xs text-ink-muted">
          No Prometheus data yet — connect the monitoring stack (see docker-compose.yml) to see
          live values here.
        </p>
      )}
    </div>
  );
}
