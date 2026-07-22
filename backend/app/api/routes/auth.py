from fastapi import APIRouter, Request

from app.api.deps import limiter

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", status_code=201)
@limiter.limit("3/hour")
async def register(request: Request):
    raise NotImplementedError


@router.post("/login")
@limiter.limit("5/minute")
async def login(request: Request):
    raise NotImplementedError


@router.post("/refresh")
async def refresh(request: Request):
    raise NotImplementedError


@router.post("/logout", status_code=204)
async def logout(request: Request):
    raise NotImplementedError
