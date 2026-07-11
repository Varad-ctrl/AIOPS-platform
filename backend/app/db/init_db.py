"""
Startup-time DB initialization: seeds the fixed set of RBAC roles if they
don't already exist. Table creation itself is handled by Alembic migrations
(see backend/alembic), not here - this only seeds reference data.
"""
from sqlalchemy.orm import Session

from app.core.logging_config import get_logger
from app.models.role import Role, RoleName

logger = get_logger("init_db")

DEFAULT_ROLES = {
    RoleName.ADMIN: "Full access to all resources and settings.",
    RoleName.DEVOPS_ENGINEER: "Access to monitoring, AI chat, and incidents.",
    RoleName.VIEWER: "Read-only access.",
}


def seed_roles(db: Session) -> None:
    for role_name, description in DEFAULT_ROLES.items():
        existing = db.query(Role).filter(Role.name == role_name.value).first()
        if not existing:
            db.add(Role(name=role_name.value, description=description))
            logger.info("role_seeded", role=role_name.value)
    db.commit()
