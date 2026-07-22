import secrets
from datetime import datetime, timedelta, timezone
from hashlib import sha256

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

# ---------------------------------------------------------------------------
# Password hashing — Argon2id (OWASP #1 recommendation for new projects)
# Memory-hard (64 MB) resists GPU/ASIC attacks; salt auto-embedded in output.
# ---------------------------------------------------------------------------
pwd_context = CryptContext(
    schemes=["argon2"],
    default="argon2",
    argon2__type="id",
    argon2__time_cost=3,
    argon2__memory_cost=65536,
    argon2__parallelism=4,
)


def hash_password(password: str) -> str:
    """Return Argon2id hash string (contains algorithm, params, salt, and hash)."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against an Argon2id hash string."""
    return pwd_context.verify(plain_password, hashed_password)


# ---------------------------------------------------------------------------
# JWT — short-lived access tokens (15 min)
# ---------------------------------------------------------------------------
def create_access_token(user_id: int, role: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    payload = {
        "sub": str(user_id),
        "role": role,
        "exp": expire,
        "type": "access",
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> dict | None:
    """Return the payload if the token is a valid access token, else None."""
    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
        if payload.get("type") != "access":
            return None
        return payload
    except JWTError:
        return None


# ---------------------------------------------------------------------------
# Opaque refresh tokens — random 32-byte string, SHA-256 hashed in DB.
# Never stored as plaintext — if DB leaks, tokens cannot be forged.
# ---------------------------------------------------------------------------
def generate_refresh_token() -> str:
    return secrets.token_urlsafe(32)


def hash_refresh_token(token: str) -> str:
    return sha256(token.encode()).hexdigest()


# ---------------------------------------------------------------------------
# CSRF token — used in double-submit cookie pattern
# ---------------------------------------------------------------------------
def generate_csrf_token() -> str:
    return secrets.token_urlsafe(32)
