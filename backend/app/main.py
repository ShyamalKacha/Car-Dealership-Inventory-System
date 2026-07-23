from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.staticfiles import StaticFiles

from app.api.routes import auth, vehicles
from app.core.config import settings
from app.core.database import Base, engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="Car Dealership API",
        description="Car Dealership Inventory System — RESTful backend",
        version="0.1.0",
        lifespan=lifespan,
        docs_url=None,  # We override /docs with self-hosted assets below
    )

    # Self-hosted Swagger UI — no CDN dependency
    app.mount("/static", StaticFiles(directory="static"), name="static")

    @app.get("/docs", include_in_schema=False)
    async def custom_swagger_ui_html():
        return get_swagger_ui_html(
            openapi_url="/openapi.json",
            title="Car Dealership API",
            swagger_js_url="/static/swagger-ui-bundle.js",
            swagger_css_url="/static/swagger-ui.css",
        )

    # CORS — configured via CORS_ORIGINS env var (JSON array of origins).
    # Defaults to localhost:5173 for development. For production, set to
    # your frontend domain(s), e.g. ["https://myapp.vercel.app"].
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def add_csp_headers(request, call_next):
        # Skip CSP for Swagger UI and its static assets so the inline
        # initializer script and favicon load without policy violations.
        if request.url.path.startswith(("/docs", "/static", "/openapi.json")):
            return await call_next(request)
        response = await call_next(request)
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data:; "
            "font-src 'self'; "
            "connect-src 'self' http://localhost:*"
        )
        return response

    app.include_router(auth.router)
    app.include_router(vehicles.router)

    return app


app = create_app()
