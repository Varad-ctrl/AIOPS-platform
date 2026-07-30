import { api } from "./api";
import type { LogSearchResponse } from "@/types";

export interface LogSearchParams {
  query?: string;
  namespace?: string;
  pod?: string;
  container?: string;
  service?: string;
  severity?: string;
  hours?: number;
  limit?: number;
}

export async function fetchRecentLogs(hours = 1, limit = 100): Promise<LogSearchResponse> {
  const { data } = await api.get<LogSearchResponse>("/logs/recent", { params: { hours, limit } });
  return data;
}

export async function searchLogs(params: LogSearchParams): Promise<LogSearchResponse> {
  const { data } = await api.get<LogSearchResponse>("/logs/search", { params });
  return data;
}

export async function fetchLogsForPod(pod: string, hours = 1, limit = 200): Promise<LogSearchResponse> {
  const { data } = await api.get<LogSearchResponse>(`/logs/pods/${encodeURIComponent(pod)}`, {
    params: { hours, limit },
  });
  return data;
}

export async function fetchLogsForContainer(
  container: string,
  hours = 1,
  limit = 200
): Promise<LogSearchResponse> {
  const { data } = await api.get<LogSearchResponse>(
    `/logs/containers/${encodeURIComponent(container)}`,
    { params: { hours, limit } }
  );
  return data;
}

export async function fetchErrorLogs(hours = 1, limit = 200): Promise<LogSearchResponse> {
  const { data } = await api.get<LogSearchResponse>("/logs/errors", { params: { hours, limit } });
  return data;
}

/** Downloads the given log entries as a plain-text file (Module 4.5). */
export function downloadLogsAsText(items: LogSearchResponse["items"], filename = "logs.txt") {
  const lines = items.map(
    (entry) =>
      `[${entry.timestamp}] (${entry.labels.container || entry.labels.service || "unknown"}) ${entry.message}`
  );
  const blob = new Blob([lines.join("\n")], { type: "text/plain" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}
