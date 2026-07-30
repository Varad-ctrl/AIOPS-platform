export type Role = "admin" | "devops_engineer" | "viewer";

export interface User {
  id: number;
  email: string;
  full_name: string;
  is_active: boolean;
  role: Role;
}

export interface Token {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface LoginPayload {
  email: string;
  password: string;
}

export interface RegisterPayload {
  email: string;
  full_name: string;
  password: string;
  role: Role;
}

// --- Phase 2: Monitoring ---

export interface MetricValue {
  metric: string;
  value: number | null;
  unit: string;
  available: boolean;
}

export interface MetricHistoryPoint {
  timestamp: string;
  value: number;
}

export interface ListResponse<T> {
  connected?: boolean;
  configured?: boolean;
  items: T[];
}

export interface K8sPod {
  name: string;
  namespace: string;
  status: string;
  node: string;
  restarts: number;
  container_count: number;
  cpu: string;
  memory: string;
}

export interface K8sNode {
  name: string;
  status: string;
  cpu_capacity: string | null;
  memory_capacity: string | null;
  kubelet_version: string | null;
}

export interface K8sDeployment {
  name: string;
  namespace: string;
  replicas: number;
  ready_replicas: number;
  available_replicas: number;
  healthy: boolean;
}

export interface ClusterHealth {
  cluster: string;
  nodes: number;
  pods: number;
  deployments: number;
  cpu_usage: number | null;
  memory_usage: number | null;
  disk_usage: number | null;
}

export interface JenkinsJob {
  name: string;
  status: string;
  url: string;
}

export interface Alert {
  id: number;
  source: string;
  severity: string;
  title: string;
  description: string;
  status: string;
  resolved: boolean;
  acknowledged_by: string;
}

export interface AlertDashboardSummary {
  active_alerts: number;
  critical: number;
  warning: number;
  resolved_today: number;
}

// --- Logs & AI ---

export interface LogEntry {
  timestamp: string;
  message: string;
  labels: Record<string, string>;
}

export interface LogSearchResponse {
  available: boolean;
  count: number;
  items: LogEntry[];
}

export interface LogSummary {
  available: boolean;
  summary: string;
  log_count: number;
}

export interface AnomalyResult {
  available: boolean;
  findings: string;
  log_count: number;
}

export interface LogAnalysisResult {
  available: boolean;
  summary: string;
  findings: string;
  log_count: number;
}

export interface RootCauseResult {
  available: boolean;
  root_cause: string;
  confidence: string;
  recommendation: string;
  evidence: string[];
  incident_id: number | null;
}

export interface IncidentSummaryResult {
  available: boolean;
  summary: string;
}

export interface RecommendationsResult {
  available: boolean;
  recommendations: string;
}

export interface AIQueryResponse {
  available: boolean;
  answer: string;
}

export interface ChatMessage {
  role: string;
  message: string;
  created_at: string;
}
