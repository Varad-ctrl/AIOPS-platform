"""
Authentication endpoints.

    POST /api/v1/auth/register  - create a new user
    POST /api/v1/auth/login     - obtain access + refresh tokens
    POST /api/v1/auth/refresh   - exchange a refresh token for a new pair
    POST /api/v1/auth/logout    - client-side token discard (stateless JWT)
    GET  /api/v1/auth/me        - current authenticated user
"""
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.core.logging_config import get_logger
from app.models.user import User
from app.schemas.auth import LoginRequest, RefreshRequest, Token
from app.schemas.user import UserCreate, UserRead
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])
logger = get_logger("auth_routes")


@router.post(
    "/register",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    responses={400: {"description": "Email already registered or unknown role"}},
)
def register(payload: UserCreate, db: Session = Depends(get_db)):
    user = AuthService(db).register(payload)
    return UserRead(id=user.id, email=user.email, full_name=user.full_name,
                     is_active=user.is_active, role=user.role.name)


@router.post(
    "/login",
    response_model=Token,
    summary="Log in and receive an access/refresh token pair",
    responses={401: {"description": "Incorrect email or password"}},
)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    service = AuthService(db)
    user = service.authenticate(payload.email, payload.password)
    return service.issue_tokens(user)


@router.post(
    "/refresh",
    response_model=Token,
    summary="Exchange a refresh token for a new access/refresh token pair",
)
def refresh(payload: RefreshRequest, db: Session = Depends(get_db)):
    return AuthService(db).refresh(payload.refresh_token)


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Log out (client discards its tokens; JWTs are stateless)",
)
def logout(current_user: User = Depends(get_current_user)):
    logger.info("logout", email=current_user.email)
    return None


@router.get(
    "/me",
    response_model=UserRead,
    summary="Get the currently authenticated user",
)
def read_current_user(current_user: User = Depends(get_current_user)):
    return UserRead(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        is_active=current_user.is_active,
        role=current_user.role.name,
    )
