"""
Authentication business logic: registration, login, token refresh.
"""
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.auth.jwt import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.core.logging_config import get_logger
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.auth import Token
from app.schemas.user import UserCreate

logger = get_logger("auth_service")


class AuthService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = UserRepository(db)

    def register(self, payload: UserCreate) -> User:
        if self.repo.get_by_email(payload.email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A user with this email already exists.",
            )

        role = self.repo.get_role_by_name(payload.role)
        if role is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unknown role '{payload.role}'.",
            )

        user = self.repo.create(
            email=payload.email,
            full_name=payload.full_name,
            hashed_password=hash_password(payload.password),
            role=role,
        )
        logger.info("user_registered", email=user.email, role=role.name)
        return user

    def authenticate(self, email: str, password: str) -> User:
        user = self.repo.get_by_email(email)
        if not user or not verify_password(password, user.hashed_password):
            logger.warning("login_failed", email=email)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password.",
            )
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This account has been deactivated.",
            )
        logger.info("login_success", email=user.email, ip="unknown")
        return user

    def issue_tokens(self, user: User) -> Token:
        access_token = create_access_token(user.email, user.role.name)
        refresh_token = create_refresh_token(user.email, user.role.name)
        return Token(access_token=access_token, refresh_token=refresh_token)

    def refresh(self, refresh_token: str) -> Token:
        payload = decode_token(refresh_token)
        if payload is None or payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token.",
            )

        user = self.repo.get_by_email(payload["sub"])
        if user is None or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User no longer exists or is inactive.",
            )

        logger.info("token_refreshed", email=user.email)
        return self.issue_tokens(user)
