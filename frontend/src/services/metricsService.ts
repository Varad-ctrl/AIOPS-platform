import { api } from "./api";
import type { MetricHistoryPoint, MetricValue } from "@/types";

export type MetricName = "cpu" | "memory" | "disk" | "network" | "load" | "filesystem";
export type HistoryMetricName = "cpu" | "memory" | "disk" | "network" | "load" | "filesystem";

export async function fetchMetric(name: MetricName): Promise<MetricValue> {
  const { data } = await api.get<MetricValue>(`/metrics/${name}`);
  return data;
}

export async function fetchAllCoreMetrics(): Promise<Record<string, MetricValue>> {
  const names: MetricName[] = ["cpu", "memory", "disk", "network"];
  const results = await Promise.all(names.map((n) => fetchMetric(n)));
  return Object.fromEntries(names.map((n, i) => [n, results[i]]));
}

export async function fetchMetricHistory(
  name: HistoryMetricName,
  hours = 24
): Promise<MetricHistoryPoint[]> {
  const { data } = await api.get<MetricHistoryPoint[]>(`/metrics/history/${name}`, {
    params: { hours },
  });
  return data;
}
