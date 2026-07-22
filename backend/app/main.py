from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.api.deps import limiter
from app.api.routes import auth, vehicles
from app.core.database import Base, engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create tables on startup — development convenience.
    Production would use Alembic migrations instead.
    """
    Base.metadata.create_all(bind=engine)
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="Car Dealership API",
        description="Car Dealership Inventory System — RESTful backend",
        version="0.1.0",
        lifespan=lifespan,
    )

    # Rate limiter
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    # CORS — restrict to frontend origin in production
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173"],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["Authorization", "Content-Type", "X-CSRF-Protection"],
    )

    # CSP headers
    @app.middleware("http")
    async def add_csp_headers(request, call_next):
        response = await call_next(request)
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data:; "
            "font-src 'self'; "
            "connect-src 'self' http://localhost:5173"
        )
        return response

    # Register routers
    app.include_router(auth.router)
    app.include_router(vehicles.router)

    return app


app = create_app()
