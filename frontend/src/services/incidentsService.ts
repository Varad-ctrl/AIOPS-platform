import { api } from "./api";

export interface Incident {
  id: number;
  alert_id: number | null;
  title: string;
  severity: string;
  status: string;
  description: string;
}

export async function fetchIncidents(status?: string): Promise<Incident[]> {
  const { data } = await api.get<Incident[]>("/incidents", { params: status ? { status } : {} });
  return data;
}

export async function updateIncidentStatus(id: number, status: string): Promise<Incident> {
  const { data } = await api.patch<Incident>(`/incidents/${id}`, { status });
  return data;
}

export async function promoteAlertToIncident(alertId: number): Promise<Incident> {
  const { data } = await api.post<Incident>(`/incidents/from-alert/${alertId}`);
  return data;
}
