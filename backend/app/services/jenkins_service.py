"""
Minimal Jenkins REST API client (no extra SDK dependency - just httpx
against Jenkins's built-in JSON API, which every Jenkins install exposes).

Degrades gracefully: if JENKINS_URL isn't configured or Jenkins is
unreachable, methods return empty lists instead of raising.
"""
from typing import Any

import httpx

from app.core.config import settings
from app.core.logging_config import get_logger

logger = get_logger("jenkins_service")


class JenkinsService:
    def __init__(
        self,
        base_url: str | None = None,
        user: str | None = None,
        api_token: str | None = None,
        timeout: float = 5.0,
    ):
        self.base_url = (base_url or settings.JENKINS_URL or "").rstrip("/")
        self.auth = (user, api_token) if user and api_token else None
        self.timeout = timeout

    @property
    def configured(self) -> bool:
        return bool(self.base_url)

    async def _get(self, path: str) -> dict[str, Any] | None:
        if not self.configured:
            return None
        url = f"{self.base_url}{path}"
        try:
            async with httpx.AsyncClient(timeout=self.timeout, auth=self.auth) as client:
                response = await client.get(url)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as exc:
            logger.warning("jenkins_request_failed", url=url, error=str(exc))
            return None

    async def get_jobs(self) -> list[dict[str, Any]]:
        data = await self._get("/api/json?tree=jobs[name,color,url]")
        if not data:
            return []
        return [
            {
                "name": job.get("name"),
                "status": _color_to_status(job.get("color", "")),
                "url": job.get("url"),
            }
            for job in data.get("jobs", [])
        ]

    async def get_builds(self, job_name: str, limit: int = 10) -> list[dict[str, Any]]:
        data = await self._get(
            f"/job/{job_name}/api/json?tree=builds[number,result,duration,timestamp]"
            f"{{0,{limit}}}"
        )
        if not data:
            return []
        return [
            {
                "job_name": job_name,
                "build_number": b.get("number"),
                "status": b.get("result") or "IN_PROGRESS",
                "duration_ms": b.get("duration", 0),
                "timestamp": b.get("timestamp"),
            }
            for b in data.get("builds", [])
        ]

    async def get_failed_builds(self) -> list[dict[str, Any]]:
        jobs = await self.get_jobs()
        failed = []
        for job in jobs:
            if job["status"] == "FAILURE":
                failed.append(job)
        return failed


def _color_to_status(color: str) -> str:
    """Jenkins encodes build status as a 'color' string on the job."""
    mapping = {
        "blue": "SUCCESS",
        "red": "FAILURE",
        "yellow": "UNSTABLE",
        "grey": "NOT_BUILT",
        "disabled": "DISABLED",
        "aborted": "ABORTED",
    }
    base_color = color.replace("_anime", "")
    return mapping.get(base_color, "UNKNOWN")
