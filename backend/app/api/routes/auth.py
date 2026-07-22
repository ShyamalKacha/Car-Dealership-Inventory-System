from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user, login_rate_limit, register_rate_limit
from app.core.config import settings
from app.core.security import create_access_token, generate_csrf_token
from app.models.user import User
from app.schemas.auth import (
    LoginRequest,
    RegisterRequest,
    UserResponse,
)
from app.services.auth_service import AuthService

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", status_code=201)
async def register(
    request: Request,
    body: RegisterRequest,
    db: Session = Depends(get_db),
    _rl: None = Depends(register_rate_limit),
):
    user = AuthService.register(db, body)
    return UserResponse.model_validate(user)


@router.post("/login")
async def login(
    request: Request,
    body: LoginRequest,
    db: Session = Depends(get_db),
    _rl: None = Depends(login_rate_limit),
):
    user = AuthService.authenticate(db, body.email, body.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    access_token = create_access_token(user.id, user.role)
    raw_refresh = AuthService.create_refresh_token(db, user.id)
    csrf_token = generate_csrf_token()

    response = JSONResponse(
        content={
            "access_token": access_token,
            "token_type": "bearer",
            "user": UserResponse.model_validate(user).model_dump(),
        }
    )
    _set_refresh_cookie(response, raw_refresh)
    _set_csrf_cookie(response, csrf_token)
    return response


@router.post("/refresh")
async def refresh(
    request: Request,
    db: Session = Depends(get_db),
):
    if request.headers.get("X-CSRF-Protection") != "1":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="CSRF validation failed",
        )

    raw_token = request.cookies.get("refresh_token")
    if not raw_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token missing",
        )

    result = AuthService.rotate_refresh_token(db, raw_token)
    if result is None:
        response = JSONResponse(
            content={"detail": "Invalid or expired refresh token"},
            status_code=status.HTTP_401_UNAUTHORIZED,
        )
        _clear_auth_cookies(response)
        return response

    new_raw_token, user_id = result
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        response = JSONResponse(
            content={"detail": "User not found"},
            status_code=status.HTTP_401_UNAUTHORIZED,
        )
        _clear_auth_cookies(response)
        return response

    access_token = create_access_token(user.id, user.role)
    csrf_token = generate_csrf_token()

    response = JSONResponse(
        content={
            "access_token": access_token,
            "token_type": "bearer",
            "user": UserResponse.model_validate(user).model_dump(),
        }
    )
    _set_refresh_cookie(response, new_raw_token)
    _set_csrf_cookie(response, csrf_token)
    return response


@router.post("/logout", status_code=204)
async def logout(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    AuthService.revoke_all_user_tokens(db, current_user.id)
    response = Response(status_code=204)
    _clear_auth_cookies(response)
    return response


# ---------------------------------------------------------------------------
# Cookie helpers
# ---------------------------------------------------------------------------
def _set_refresh_cookie(response: Response, value: str) -> None:
    response.set_cookie(
        key="refresh_token",
        value=value,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite="lax",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
    )


def _set_csrf_cookie(response: Response, value: str) -> None:
    response.set_cookie(
        key="csrf_token",
        value=value,
        httponly=False,
        secure=settings.COOKIE_SECURE,
        samesite="lax",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
    )


def _clear_auth_cookies(response: Response) -> None:
    response.delete_cookie("refresh_token")
    response.delete_cookie("csrf_token")
