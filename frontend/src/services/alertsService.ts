import { api } from "./api";
import type { Alert, AlertDashboardSummary } from "@/types";

export async function fetchAllAlerts(): Promise<Alert[]> {
  const { data } = await api.get<Alert[]>("/alerts");
  return data;
}

export async function fetchActiveAlerts(): Promise<Alert[]> {
  const { data } = await api.get<Alert[]>("/alerts/active");
  return data;
}

export async function fetchAlertDashboard(): Promise<AlertDashboardSummary> {
  const { data } = await api.get<AlertDashboardSummary>("/alerts/dashboard");
  return data;
}

export async function acknowledgeAlert(alertId: number): Promise<Alert> {
  const { data } = await api.post<Alert>(`/alerts/${alertId}/acknowledge`, {});
  return data;
}

export async function resolveAlert(alertId: number): Promise<Alert> {
  const { data } = await api.post<Alert>(`/alerts/${alertId}/resolve`);
  return data;
}
