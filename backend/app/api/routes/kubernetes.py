"""
Kubernetes cluster introspection endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.auth.rbac import require_any_role
from app.services.kubernetes_service import KubernetesService

router = APIRouter(prefix="/kubernetes", tags=["Kubernetes"])


def get_kubernetes_service() -> KubernetesService:
    return KubernetesService()


@router.get("/pods", summary="List pods (optionally filtered by namespace)",
            dependencies=[Depends(require_any_role)])
def list_pods(
    namespace: str | None = Query(default=None),
    k8s: KubernetesService = Depends(get_kubernetes_service),
):
    return {"connected": k8s.connected, "items": k8s.get_pods(namespace)}


@router.get("/pods/{pod_name}", summary="Get a single pod's metrics",
            dependencies=[Depends(require_any_role)])
def get_pod(
    pod_name: str,
    namespace: str = Query(default="default"),
    k8s: KubernetesService = Depends(get_kubernetes_service),
):
    pod = k8s.get_pod(pod_name, namespace)
    if pod is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pod not found")
    return pod


@router.get("/nodes", summary="List cluster nodes",
            dependencies=[Depends(require_any_role)])
def list_nodes(k8s: KubernetesService = Depends(get_kubernetes_service)):
    return {"connected": k8s.connected, "items": k8s.get_nodes()}


@router.get("/deployments", summary="List deployments",
            dependencies=[Depends(require_any_role)])
def list_deployments(
    namespace: str | None = Query(default=None),
    k8s: KubernetesService = Depends(get_kubernetes_service),
):
    return {"connected": k8s.connected, "items": k8s.get_deployments(namespace)}


@router.get("/namespaces", summary="List namespaces",
            dependencies=[Depends(require_any_role)])
def list_namespaces(k8s: KubernetesService = Depends(get_kubernetes_service)):
    return {"connected": k8s.connected, "items": k8s.get_namespaces()}


@router.get("/services", summary="List services",
            dependencies=[Depends(require_any_role)])
def list_services(
    namespace: str | None = Query(default=None),
    k8s: KubernetesService = Depends(get_kubernetes_service),
):
    return {"connected": k8s.connected, "items": k8s.get_services(namespace)}


@router.get("/replicasets", summary="List replica sets",
            dependencies=[Depends(require_any_role)])
def list_replicasets(
    namespace: str | None = Query(default=None),
    k8s: KubernetesService = Depends(get_kubernetes_service),
):
    return {"connected": k8s.connected, "items": k8s.get_replicasets(namespace)}


@router.get("/statefulsets", summary="List stateful sets",
            dependencies=[Depends(require_any_role)])
def list_statefulsets(
    namespace: str | None = Query(default=None),
    k8s: KubernetesService = Depends(get_kubernetes_service),
):
    return {"connected": k8s.connected, "items": k8s.get_statefulsets(namespace)}
