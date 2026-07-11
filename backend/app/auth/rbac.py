"""
Role-Based Access Control (RBAC).

Usage in a route:

    @router.get("/incidents", dependencies=[Depends(require_roles("admin", "devops_engineer"))])
    def list_incidents(): ...

Roles:
    admin            -> full access
    devops_engineer  -> monitoring, AI chat, incidents
    viewer           -> read-only
"""
from fastapi import Depends, HTTPException, status

from app.api.deps import get_current_user
from app.models.user import User


def require_roles(*allowed_roles: str):
    def dependency(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role.name not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{current_user.role.name}' is not permitted to perform this action.",
            )
        return current_user

    return dependency


# Convenience shortcuts matching the permission matrix in the roadmap.
require_admin = require_roles("admin")
require_devops_or_admin = require_roles("admin", "devops_engineer")
require_any_role = require_roles("admin", "devops_engineer", "viewer")
