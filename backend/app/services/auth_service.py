from datetime import datetime, timedelta, timezone
from uuid import uuid4

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import (
    generate_refresh_token,
    hash_password,
    hash_refresh_token,
    verify_password,
)
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.schemas.auth import RegisterRequest


class AuthService:
    """Business logic for authentication — register, login, refresh, logout."""

    @staticmethod
    def register(db: Session, request: RegisterRequest) -> User:
        """Register a new user. Returns the created User or raises 409/422."""

        existing = db.query(User).filter(User.email == request.email).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered",
            )

        role = "admin" if request.admin_key == settings.ADMIN_SECRET_KEY else "user"

        user = User(
            email=request.email,
            username=request.username,
            hashed_password=hash_password(request.password),
            role=role,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def authenticate(db: Session, email: str, password: str) -> User | None:
        """Return the User if credentials are valid, else None.
        Uses the same generic message for wrong-email and wrong-password
        to prevent email enumeration.
        """
        user = db.query(User).filter(User.email == email).first()
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user

    # ------------------------------------------------------------------
    # Refresh token management
    # ------------------------------------------------------------------
    @staticmethod
    def create_refresh_token(db: Session, user_id: int) -> str:
        """Generate an opaque refresh token, store SHA-256 hash in DB,
        and return the raw token string (to be set as a cookie)."""
        raw_token = generate_refresh_token()
        token_hash = hash_refresh_token(raw_token)
        family_id = str(uuid4())
        expires_at = datetime.now(timezone.utc) + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )

        db_token = RefreshToken(
            user_id=user_id,
            token_hash=token_hash,
            family_id=family_id,
            expires_at=expires_at,
        )
        db.add(db_token)
        db.commit()
        return raw_token

    @staticmethod
    def rotate_refresh_token(db: Session, raw_token: str) -> tuple[str, int] | None:
        """Rotate a refresh token.
        Returns (new_raw_token, user_id) on success.
        Returns None if token is invalid, expired, or reuse is detected.
        On reuse detection the entire token family is revoked.
        """
        token_hash = hash_refresh_token(raw_token)
        existing = (
            db.query(RefreshToken)
            .filter(RefreshToken.token_hash == token_hash)
            .first()
        )

        if not existing:
            return None

        # Reuse detection — a revoked token was presented
        if existing.is_revoked:
            # Revoke all tokens in this family
            db.query(RefreshToken).filter(
                RefreshToken.family_id == existing.family_id,
                RefreshToken.is_revoked == False,
            ).update({"is_revoked": True})
            db.commit()
            return None

        # Expired
        if existing.expires_at.replace(tzinfo=timezone.utc) < datetime.now(
            timezone.utc
        ):
            return None

        user_id = existing.user_id

        # Revoke old token
        existing.is_revoked = True

        # Issue new token (same family_id)
        new_raw = generate_refresh_token()
        new_hash = hash_refresh_token(new_raw)
        expires_at = datetime.now(timezone.utc) + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )

        db.add(
            RefreshToken(
                user_id=user_id,
                token_hash=new_hash,
                family_id=existing.family_id,
                expires_at=expires_at,
            )
        )
        db.commit()
        return new_raw, user_id

    @staticmethod
    def revoke_all_user_tokens(db: Session, user_id: int) -> None:
        """Revoke every non-revoked refresh token belonging to a user."""
        db.query(RefreshToken).filter(
            RefreshToken.user_id == user_id,
            RefreshToken.is_revoked == False,
        ).update({"is_revoked": True})
        db.commit()
