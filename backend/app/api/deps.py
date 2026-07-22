import os

from collections.abc import Generator

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.core.security import decode_access_token
from app.models.user import User

# ---------------------------------------------------------------------------
# Rate limiter — IP-based, in-memory counters (single-server)
# Disabled during tests via TESTING env var.
# ---------------------------------------------------------------------------
limiter = Limiter(
    key_func=get_remote_address,
    enabled=not os.getenv("TESTING"),
)

# ---------------------------------------------------------------------------
# HTTP Bearer scheme — auto-extracts token from Authorization header
# ---------------------------------------------------------------------------
security_scheme = HTTPBearer(auto_error=False)


# ---------------------------------------------------------------------------
# Database session — guaranteed cleanup via finally
# ---------------------------------------------------------------------------
def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Current user extraction — validates JWT, returns User or raises 401
# ---------------------------------------------------------------------------
def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security_scheme),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )

    payload = decode_access_token(credentials.credentials)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    user = db.query(User).filter(User.id == int(payload["sub"])).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    return user


# ---------------------------------------------------------------------------
# Admin guard — layered on top of get_current_user
# ---------------------------------------------------------------------------
def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )
    return current_user
