import { api } from "./api";
import type { MetricHistoryPoint, MetricValue } from "@/types";

export type MetricName = "cpu" | "memory" | "disk" | "network" | "load" | "filesystem";
export type HistoryMetricName = "cpu" | "memory" | "disk" | "network" | "load" | "filesystem";

export async function fetchMetric(name: MetricName): Promise<MetricValue> {
  try {
    console.log("Fetching:", name);

    const { data } = await api.get<MetricValue>(`/metrics/${name}`);

    console.log("Response:", name, data);

    return data;
  } catch (err) {
    console.error("Failed:", name, err);
    throw err;
  }
}

export async function fetchAllCoreMetrics() {
  const names: MetricName[] = [
    "cpu",
    "memory",
    "disk",
    "network",
  ];

  const results = await Promise.allSettled(
    names.map((name) => fetchMetric(name))
  );

  return Object.fromEntries(
    names.map((name, index) => [
      name,
      results[index].status === "fulfilled"
        ? results[index].value
        : {
            metric: name,
            value: null,
            unit: "",
            available: false,
          },
    ])
  );
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
