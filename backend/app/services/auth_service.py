from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.auth import RegisterRequest


class AuthService:
    """Business logic for authentication — register, login, refresh, logout.
    Implementations are stubs for RED phase; wired in GREEN commit.
    """

    @staticmethod
    def register(db: Session, request: RegisterRequest) -> User:
        raise NotImplementedError

    @staticmethod
    def authenticate(db: Session, email: str, password: str) -> User | None:
        raise NotImplementedError

    @staticmethod
    def create_refresh_token(db: Session, user_id: int) -> tuple[str, str]:
        """Return (raw_token, cookie_value) — cookie value includes prefix if needed."""
        raise NotImplementedError

    @staticmethod
    def rotate_refresh_token(
        db: Session, raw_token: str
    ) -> tuple[str, str] | None:
        """Return (new_raw_token, new_cookie_value) or None if invalid/reuse detected."""
        raise NotImplementedError

    @staticmethod
    def revoke_all_user_tokens(db: Session, user_id: int) -> None:
        raise NotImplementedError
