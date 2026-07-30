"""
Application entrypoint.

Run locally with:
    uvicorn app.main:app --reload

Swagger UI:  http://localhost:8000/docs
ReDoc:       http://localhost:8000/redoc
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import (
    ai,
    alerts,
    auth,
    cluster,
    health,
    incidents,
    jenkins,
    kubernetes,
    logs,
    metrics,
    self_metrics,
    users,
)
from app.core.config import settings
from app.core.logging_config import configure_logging, get_logger
from app.core.scheduler import start_scheduler, stop_scheduler
from app.db.init_db import seed_roles
from app.db.session import SessionLocal
from app.middleware.logging_middleware import RequestLoggingMiddleware

configure_logging()
logger = get_logger("main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("startup", environment=settings.ENVIRONMENT)
    db = SessionLocal()
    try:
        seed_roles(db)
    finally:
        db.close()
    start_scheduler()
    yield
    stop_scheduler()
    logger.info("shutdown")


tags_metadata = [
    {"name": "Authentication", "description": "Register, log in, refresh, and log out."},
    {"name": "Users", "description": "User management, protected by RBAC."},
    {"name": "Health", "description": "Liveness and readiness probes."},
    {"name": "Metrics", "description": "Live and historical infrastructure metrics (Prometheus-backed)."},
    {"name": "Kubernetes", "description": "Cluster, pod, node, and deployment introspection."},
    {"name": "Cluster", "description": "Aggregate cluster health snapshot."},
    {"name": "Jenkins", "description": "CI/CD job and build status."},
    {"name": "Alerts", "description": "Alert history, active alerts, and the Alertmanager webhook receiver."},
    {"name": "Incidents", "description": "Human-tracked incidents, optionally promoted from alerts."},
    {"name": "Logs", "description": "Log search and retrieval, backed by Loki."},
    {"name": "AI Insights", "description": "AI-powered log analysis, root cause analysis, recommendations, and natural language chat."},
]

app = FastAPI(
    title=settings.PROJECT_NAME,
    description=(
        "AI-Powered AIOps Assistant API - Phase 1 (JWT auth + RBAC), Phase 2 "
        "(Prometheus, Kubernetes, Jenkins, alert lifecycle, incidents), Phase 3/4 "
        "(Loki log search + observability dashboards), and Phase 5 (LLM-powered "
        "root cause analysis, recommendations, and natural language chat) are "
        "all live."
    ),
    version="0.5.0",
    openapi_tags=tags_metadata,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# --- Middleware ---
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Routers ---
app.include_router(health.router, prefix=settings.API_V1_PREFIX)
app.include_router(auth.router, prefix=settings.API_V1_PREFIX)
app.include_router(users.router, prefix=settings.API_V1_PREFIX)
app.include_router(self_metrics.router, prefix=settings.API_V1_PREFIX)
app.include_router(metrics.router, prefix=settings.API_V1_PREFIX)
app.include_router(kubernetes.router, prefix=settings.API_V1_PREFIX)
app.include_router(cluster.router, prefix=settings.API_V1_PREFIX)
app.include_router(jenkins.router, prefix=settings.API_V1_PREFIX)
app.include_router(alerts.router, prefix=settings.API_V1_PREFIX)
app.include_router(incidents.router, prefix=settings.API_V1_PREFIX)
app.include_router(logs.router, prefix=settings.API_V1_PREFIX)
app.include_router(ai.router, prefix=settings.API_V1_PREFIX)


@app.get("/", tags=["Health"], summary="Root")
def root():
    return {
        "service": settings.PROJECT_NAME,
        "status": "running",
        "docs": "/docs",
    }
