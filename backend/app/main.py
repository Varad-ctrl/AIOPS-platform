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

from app.api.routes import auth, health, users
from app.core.config import settings
from app.core.logging_config import configure_logging, get_logger
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
    yield
    logger.info("shutdown")


tags_metadata = [
    {"name": "Authentication", "description": "Register, log in, refresh, and log out."},
    {"name": "Users", "description": "User management, protected by RBAC."},
    {"name": "Health", "description": "Liveness and readiness probes."},
]

app = FastAPI(
    title=settings.PROJECT_NAME,
    description=(
        "AI-Powered AIOps Assistant API - Phase 1: secure application "
        "foundation with JWT authentication and role-based access control. "
        "Later phases add observability, log intelligence, an AI agent, "
        "incident detection, root-cause analysis, and alerting."
    ),
    version="0.1.0",
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


@app.get("/", tags=["Health"], summary="Root")
def root():
    return {
        "service": settings.PROJECT_NAME,
        "status": "running",
        "docs": "/docs",
    }
