import { useState } from "react";
import StatusBadge from "@/components/StatusBadge";
import { usePolling } from "@/hooks/usePolling";
import { fetchDeployments, fetchNodes, fetchPods } from "@/services/kubernetesService";

type Tab = "pods" | "nodes" | "deployments";

export default function Kubernetes() {
  const [tab, setTab] = useState<Tab>("pods");
  const { data: pods } = usePolling(() => fetchPods(), 15000);
  const { data: nodes } = usePolling(() => fetchNodes(), 20000);
  const { data: deployments } = usePolling(() => fetchDeployments(), 20000);

  const connected = pods?.connected ?? false;

  return (
    <div className="space-y-6">
      <div>
        <p className="label-eyebrow">Cluster</p>
        <h1 className="text-xl font-semibold text-ink-primary mt-1">Kubernetes</h1>
        <p className="text-sm text-ink-secondary mt-1">
          Pods, nodes, and deployments across all namespaces.
        </p>
      </div>

      {!connected && (
        <div className="panel p-4 text-sm text-ink-secondary">
          Not connected to a cluster. Set a kubeconfig or run the backend in-cluster to see live
          objects here.
        </div>
      )}

      <div className="flex gap-2">
        {(["pods", "nodes", "deployments"] as Tab[]).map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`px-3 py-1.5 rounded text-sm font-medium capitalize transition ${
              tab === t
                ? "bg-base-800 text-accent border border-base-600"
                : "text-ink-secondary hover:text-ink-primary border border-transparent"
            }`}
          >
            {t}
          </button>
        ))}
      </div>

      {tab === "pods" && (
        <div className="panel overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-base-700 text-ink-muted text-left">
                <th className="px-4 py-3 font-medium">Name</th>
                <th className="px-4 py-3 font-medium">Namespace</th>
                <th className="px-4 py-3 font-medium">Status</th>
                <th className="px-4 py-3 font-medium">Restarts</th>
                <th className="px-4 py-3 font-medium">CPU</th>
                <th className="px-4 py-3 font-medium">Memory</th>
              </tr>
            </thead>
            <tbody>
              {(pods?.items ?? []).map((pod) => (
                <tr key={`${pod.namespace}/${pod.name}`} className="border-b border-base-700 last:border-0">
                  <td className="px-4 py-3 text-ink-primary font-mono">{pod.name}</td>
                  <td className="px-4 py-3 text-ink-secondary">{pod.namespace}</td>
                  <td className="px-4 py-3">
                    <StatusBadge status={pod.status} />
                  </td>
                  <td className="px-4 py-3 text-ink-secondary">{pod.restarts}</td>
                  <td className="px-4 py-3 text-ink-secondary">{pod.cpu}</td>
                  <td className="px-4 py-3 text-ink-secondary">{pod.memory}</td>
                </tr>
              ))}
              {(pods?.items ?? []).length === 0 && (
                <tr>
                  <td colSpan={6} className="px-4 py-8 text-center text-ink-muted">
                    No pods found
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}

      {tab === "nodes" && (
        <div className="panel overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-base-700 text-ink-muted text-left">
                <th className="px-4 py-3 font-medium">Name</th>
                <th className="px-4 py-3 font-medium">Status</th>
                <th className="px-4 py-3 font-medium">CPU capacity</th>
                <th className="px-4 py-3 font-medium">Memory capacity</th>
                <th className="px-4 py-3 font-medium">Kubelet</th>
              </tr>
            </thead>
            <tbody>
              {(nodes?.items ?? []).map((node) => (
                <tr key={node.name} className="border-b border-base-700 last:border-0">
                  <td className="px-4 py-3 text-ink-primary font-mono">{node.name}</td>
                  <td className="px-4 py-3">
                    <StatusBadge status={node.status} />
                  </td>
                  <td className="px-4 py-3 text-ink-secondary">{node.cpu_capacity ?? "—"}</td>
                  <td className="px-4 py-3 text-ink-secondary">{node.memory_capacity ?? "—"}</td>
                  <td className="px-4 py-3 text-ink-secondary">{node.kubelet_version ?? "—"}</td>
                </tr>
              ))}
              {(nodes?.items ?? []).length === 0 && (
                <tr>
                  <td colSpan={5} className="px-4 py-8 text-center text-ink-muted">
                    No nodes found
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}

      {tab === "deployments" && (
        <div className="panel overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-base-700 text-ink-muted text-left">
                <th className="px-4 py-3 font-medium">Name</th>
                <th className="px-4 py-3 font-medium">Namespace</th>
                <th className="px-4 py-3 font-medium">Replicas</th>
                <th className="px-4 py-3 font-medium">Ready</th>
                <th className="px-4 py-3 font-medium">Health</th>
              </tr>
            </thead>
            <tbody>
              {(deployments?.items ?? []).map((d) => (
                <tr key={`${d.namespace}/${d.name}`} className="border-b border-base-700 last:border-0">
                  <td className="px-4 py-3 text-ink-primary font-mono">{d.name}</td>
                  <td className="px-4 py-3 text-ink-secondary">{d.namespace}</td>
                  <td className="px-4 py-3 text-ink-secondary">{d.replicas}</td>
                  <td className="px-4 py-3 text-ink-secondary">{d.ready_replicas}</td>
                  <td className="px-4 py-3">
                    <StatusBadge status={d.healthy ? "Healthy" : "Degraded"} />
                  </td>
                </tr>
              ))}
              {(deployments?.items ?? []).length === 0 && (
                <tr>
                  <td colSpan={5} className="px-4 py-8 text-center text-ink-muted">
                    No deployments found
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
