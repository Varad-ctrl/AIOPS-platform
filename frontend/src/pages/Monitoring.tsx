import EmptyState from "@/components/EmptyState";

export default function Monitoring() {
  return (
    <EmptyState
      eyebrow="Observability"
      title="Live metrics dashboard"
      description="CPU, memory, disk, network, and Kubernetes pod/node health will render here once Prometheus, Node Exporter, and kube-state-metrics are wired up."
      phase="Phase 2"
    />
  );
}
