"""
Liveness/readiness endpoint used by Docker, Kubernetes, and load balancers.
"""
from fastapi import APIRouter, Depends, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.deps import get_db

router = APIRouter(tags=["Health"])


@router.get(
    "/health",
    summary="Health check",
    status_code=status.HTTP_200_OK,
)
def health_check():
    return {"status": "healthy"}


@router.get(
    "/health/db",
    summary="Health check including a database round-trip",
)
def health_check_db(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    return {"status": "healthy", "database": "connected"}
