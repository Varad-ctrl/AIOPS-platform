"""
Jenkins job/build introspection endpoints.
"""
from fastapi import APIRouter, Depends, Query

from app.auth.rbac import require_any_role
from app.core.config import settings
from app.services.jenkins_service import JenkinsService

router = APIRouter(prefix="/jenkins", tags=["Jenkins"])


def get_jenkins_service() -> JenkinsService:
    return JenkinsService(user=settings.JENKINS_USER or None, api_token=settings.JENKINS_API_TOKEN or None)


@router.get("/jobs", summary="List Jenkins jobs and their status",
            dependencies=[Depends(require_any_role)])
async def list_jobs(jenkins: JenkinsService = Depends(get_jenkins_service)):
    return {"configured": jenkins.configured, "items": await jenkins.get_jobs()}


@router.get("/builds", summary="List recent builds for a job",
            dependencies=[Depends(require_any_role)])
async def list_builds(
    job_name: str = Query(..., description="Jenkins job name"),
    limit: int = Query(default=10, ge=1, le=100),
    jenkins: JenkinsService = Depends(get_jenkins_service),
):
    return {
        "configured": jenkins.configured,
        "items": await jenkins.get_builds(job_name, limit=limit),
    }


@router.get("/failed", summary="List jobs whose last build failed",
            dependencies=[Depends(require_any_role)])
async def list_failed(jenkins: JenkinsService = Depends(get_jenkins_service)):
    return {"configured": jenkins.configured, "items": await jenkins.get_failed_builds()}
