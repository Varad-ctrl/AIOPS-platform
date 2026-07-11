"""
User management endpoints. Demonstrates RBAC in practice:

    GET  /api/v1/users        -> admin only
    GET  /api/v1/users/{id}   -> admin or devops_engineer
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.auth.rbac import require_admin, require_devops_or_admin
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserRead

router = APIRouter(prefix="/users", tags=["Users"])


@router.get(
    "",
    response_model=list[UserRead],
    summary="List all users (admin only)",
    dependencies=[Depends(require_admin)],
)
def list_users(db: Session = Depends(get_db)):
    users = UserRepository(db).list_all()
    return [
        UserRead(id=u.id, email=u.email, full_name=u.full_name, is_active=u.is_active, role=u.role.name)
        for u in users
    ]


@router.get(
    "/{user_id}",
    response_model=UserRead,
    summary="Get a single user (admin or devops_engineer)",
    dependencies=[Depends(require_devops_or_admin)],
)
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = UserRepository(db).get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return UserRead(id=user.id, email=user.email, full_name=user.full_name,
                     is_active=user.is_active, role=user.role.name)
