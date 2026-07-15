import { api } from "./api";
import type { ClusterHealth, K8sDeployment, K8sNode, K8sPod, ListResponse } from "@/types";

export async function fetchPods(namespace?: string): Promise<ListResponse<K8sPod>> {
  const { data } = await api.get<ListResponse<K8sPod>>("/kubernetes/pods", {
    params: namespace ? { namespace } : {},
  });
  return data;
}

export async function fetchNodes(): Promise<ListResponse<K8sNode>> {
  const { data } = await api.get<ListResponse<K8sNode>>("/kubernetes/nodes");
  return data;
}

export async function fetchDeployments(namespace?: string): Promise<ListResponse<K8sDeployment>> {
  const { data } = await api.get<ListResponse<K8sDeployment>>("/kubernetes/deployments", {
    params: namespace ? { namespace } : {},
  });
  return data;
}

export async function fetchClusterHealth(): Promise<ClusterHealth> {
  const { data } = await api.get<ClusterHealth>("/cluster/health");
  return data;
}
