"""
Wraps the official `kubernetes` Python client.

Loads config in this order:
    1. In-cluster config (when running as a pod with a service account)
    2. Local kubeconfig (~/.kube/config) - useful when developing against
       a Kind/minikube/OpenShift cluster from outside the container

If neither is available (e.g. this stack is running standalone with no
cluster attached), every method degrades gracefully and returns an empty
result with `available: False` rather than raising - the dashboard shows
"cluster not connected" instead of crashing.
"""
from typing import Any
from app.core.config import settings
from app.core.logging_config import get_logger

logger = get_logger("kubernetes_service")

try:
    from kubernetes import client, config
    from kubernetes.client.rest import ApiException

    _KUBERNETES_LIB_AVAILABLE = True
except ImportError:  # pragma: no cover - exercised only if dependency missing
    _KUBERNETES_LIB_AVAILABLE = False


class KubernetesService:
    def __init__(self):
        self.connected = False
        self.core_v1 = None
        self.apps_v1 = None

        if not _KUBERNETES_LIB_AVAILABLE:
            logger.warning("kubernetes_client_not_installed")
            return

        try:
            try:
                config.load_incluster_config()
                logger.info(
                    "kubernetes_config_loaded",
                    source="in-cluster",
                )
            except Exception:
                config.load_kube_config(
                    context=settings.KUBE_CONTEXT
                )
                logger.info(
                    "kubernetes_config_loaded",
                    source="kubeconfig",
                    context=settings.KUBE_CONTEXT,
                )

            self.core_v1 = client.CoreV1Api()
            self.apps_v1 = client.AppsV1Api()
            self.connected = True

        except Exception as exc:
            logger.warning(
                "kubernetes_not_connected",
                error=str(exc),
            )
            self.connected = False

    def get_pods(self, namespace: str | None = None) -> list[dict[str, Any]]:
        if not self.connected:
            return []
        try:
            pods = (
                self.core_v1.list_namespaced_pod(namespace)
                if namespace
                else self.core_v1.list_pod_for_all_namespaces()
            )
            return [self._serialize_pod(p) for p in pods.items]
        except ApiException as exc:
            logger.warning("k8s_get_pods_failed", error=str(exc))
            return []

    def get_pod(self, pod_name: str, namespace: str = "default") -> dict[str, Any] | None:
        if not self.connected:
            return None
        try:
            pod = self.core_v1.read_namespaced_pod(pod_name, namespace)
            return self._serialize_pod(pod)
        except ApiException as exc:
            logger.warning("k8s_get_pod_failed", pod=pod_name, error=str(exc))
            return None

    def get_nodes(self) -> list[dict[str, Any]]:
        if not self.connected:
            return []
        try:
            nodes = self.core_v1.list_node()
            result = []
            for n in nodes.items:
                conditions = {c.type: c.status for c in (n.status.conditions or [])}
                result.append(
                    {
                        "name": n.metadata.name,
                        "status": "Ready" if conditions.get("Ready") == "True" else "NotReady",
                        "cpu_capacity": n.status.capacity.get("cpu") if n.status.capacity else None,
                        "memory_capacity": n.status.capacity.get("memory")
                        if n.status.capacity
                        else None,
                        "kubelet_version": n.status.node_info.kubelet_version
                        if n.status.node_info
                        else None,
                    }
                )
            return result
        except ApiException as exc:
            logger.warning("k8s_get_nodes_failed", error=str(exc))
            return []

    def get_deployments(self, namespace: str | None = None) -> list[dict[str, Any]]:
        if not self.connected:
            return []
        try:
            deployments = (
                self.apps_v1.list_namespaced_deployment(namespace)
                if namespace
                else self.apps_v1.list_deployment_for_all_namespaces()
            )
            return [
                {
                    "name": d.metadata.name,
                    "namespace": d.metadata.namespace,
                    "replicas": d.spec.replicas,
                    "ready_replicas": d.status.ready_replicas or 0,
                    "available_replicas": d.status.available_replicas or 0,
                    "healthy": (d.status.ready_replicas or 0) == (d.spec.replicas or 0),
                }
                for d in deployments.items
            ]
        except ApiException as exc:
            logger.warning("k8s_get_deployments_failed", error=str(exc))
            return []

    def get_namespaces(self) -> list[str]:
        if not self.connected:
            return []
        try:
            namespaces = self.core_v1.list_namespace()
            return [ns.metadata.name for ns in namespaces.items]
        except ApiException as exc:
            logger.warning("k8s_get_namespaces_failed", error=str(exc))
            return []

    def get_services(self, namespace: str | None = None) -> list[dict[str, Any]]:
        if not self.connected:
            return []
        try:
            services = (
                self.core_v1.list_namespaced_service(namespace)
                if namespace
                else self.core_v1.list_service_for_all_namespaces()
            )
            return [
                {
                    "name": s.metadata.name,
                    "namespace": s.metadata.namespace,
                    "type": s.spec.type,
                    "cluster_ip": s.spec.cluster_ip,
                    "ports": [p.port for p in (s.spec.ports or [])],
                }
                for s in services.items
            ]
        except ApiException as exc:
            logger.warning("k8s_get_services_failed", error=str(exc))
            return []

    def get_replicasets(self, namespace: str | None = None) -> list[dict[str, Any]]:
        if not self.connected:
            return []
        try:
            rs = (
                self.apps_v1.list_namespaced_replica_set(namespace)
                if namespace
                else self.apps_v1.list_replica_set_for_all_namespaces()
            )
            return [
                {
                    "name": r.metadata.name,
                    "namespace": r.metadata.namespace,
                    "replicas": r.spec.replicas,
                    "ready_replicas": r.status.ready_replicas or 0,
                }
                for r in rs.items
            ]
        except ApiException as exc:
            logger.warning("k8s_get_replicasets_failed", error=str(exc))
            return []

    def get_statefulsets(self, namespace: str | None = None) -> list[dict[str, Any]]:
        if not self.connected:
            return []
        try:
            sts = (
                self.apps_v1.list_namespaced_stateful_set(namespace)
                if namespace
                else self.apps_v1.list_stateful_set_for_all_namespaces()
            )
            return [
                {
                    "name": s.metadata.name,
                    "namespace": s.metadata.namespace,
                    "replicas": s.spec.replicas,
                    "ready_replicas": s.status.ready_replicas or 0,
                }
                for s in sts.items
            ]
        except ApiException as exc:
            logger.warning("k8s_get_statefulsets_failed", error=str(exc))
            return []

    def cluster_summary(self) -> dict[str, Any]:
        """Powers GET /cluster/health."""
        if not self.connected:
            return {"cluster": "Disconnected", "nodes": 0, "pods": 0, "deployments": 0}

        nodes = self.get_nodes()
        pods = self.get_pods()
        deployments = self.get_deployments()
        all_ready = all(n["status"] == "Ready" for n in nodes) if nodes else False

        return {
            "cluster": "Healthy" if all_ready else "Degraded",
            "nodes": len(nodes),
            "pods": len(pods),
            "deployments": len(deployments),
        }

    @staticmethod
    def _serialize_pod(pod) -> dict[str, Any]:
        container_statuses = pod.status.container_statuses or []
        restarts = sum(c.restart_count for c in container_statuses)
        return {
            "name": pod.metadata.name,
            "namespace": pod.metadata.namespace,
            "status": pod.status.phase,
            "node": pod.spec.node_name,
            "restarts": restarts,
            "container_count": len(pod.spec.containers or []),
            "cpu": _sum_resource(pod, "cpu"),
            "memory": _sum_resource(pod, "memory"),
        }


def _sum_resource(pod, resource: str) -> str:
    """Best-effort sum of requested resources across containers (e.g. '250m', '512Mi')."""
    try:
        total = 0.0
        unit = ""
        for c in pod.spec.containers or []:
            requests = (c.resources.requests or {}) if c.resources else {}
            raw = requests.get(resource)
            if not raw:
                continue
            digits = "".join(ch for ch in raw if ch.isdigit() or ch == ".")
            unit = "".join(ch for ch in raw if not (ch.isdigit() or ch == "."))
            if digits:
                total += float(digits)
        if not total:
            return "n/a"
        return f"{int(total) if total.is_integer() else total}{unit}"
    except Exception:
        return "n/a"
