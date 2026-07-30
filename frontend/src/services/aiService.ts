import { api } from "./api";
import type {
  AIQueryResponse,
  AnomalyResult,
  ChatMessage,
  IncidentSummaryResult,
  LogAnalysisResult,
  LogSummary,
  RecommendationsResult,
  RootCauseResult,
} from "@/types";

export async function summarizeLogs(namespace?: string, pod?: string, hours = 1): Promise<LogSummary> {
  const { data } = await api.get<LogSummary>("/ai/logs/summary", {
    params: { namespace, pod, hours },
  });
  return data;
}

export async function detectAnomalies(
  namespace?: string,
  pod?: string,
  hours = 1
): Promise<AnomalyResult> {
  const { data } = await api.get<AnomalyResult>("/ai/logs/anomalies", {
    params: { namespace, pod, hours },
  });
  return data;
}

export async function analyzeLogs(
  namespace?: string,
  pod?: string,
  hours = 1
): Promise<LogAnalysisResult> {
  const { data } = await api.post<LogAnalysisResult>("/ai/log-analysis", {
    namespace,
    pod,
    hours,
  });
  return data;
}

export async function rootCauseForIncident(incidentId: number): Promise<RootCauseResult> {
  const { data } = await api.post<RootCauseResult>(`/ai/incidents/${incidentId}/root-cause`);
  return data;
}

export async function rootCauseFreeform(description: string): Promise<RootCauseResult> {
  const { data } = await api.post<RootCauseResult>("/ai/root-cause", { description });
  return data;
}

export async function incidentSummary(incidentId: number): Promise<IncidentSummaryResult> {
  const { data } = await api.post<IncidentSummaryResult>("/ai/incident-summary", {
    incident_id: incidentId,
  });
  return data;
}

export async function fetchRecommendations(): Promise<RecommendationsResult> {
  const { data } = await api.post<RecommendationsResult>("/ai/recommendations");
  return data;
}

export async function askAI(question: string): Promise<AIQueryResponse> {
  const { data } = await api.post<AIQueryResponse>("/ai/chat", { question });
  return data;
}

export async function fetchChatHistory(): Promise<ChatMessage[]> {
  const { data } = await api.get<ChatMessage[]>("/ai/chat/history");
  return data;
}
