import sentry_sdk
from fastapi import FastAPI
from fastapi.routing import APIRoute
from starlette.middleware.cors import CORSMiddleware

from app.api.main import api_router
from app.core.config import settings
from app.core.metrics import create_instrumentator, initialize_application_info


def custom_generate_unique_id(route: APIRoute) -> str:
    return f"{route.tags[0]}-{route.name}"


if settings.SENTRY_DSN and settings.ENVIRONMENT != "local":
    sentry_sdk.init(dsn=str(settings.SENTRY_DSN), enable_tracing=True)

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    generate_unique_id_function=custom_generate_unique_id,
)

# Set all CORS enabled origins
if settings.all_cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.all_cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# ============================================================================
# Prometheus Metrics Instrumentation
# ============================================================================

# Create and configure Prometheus instrumentator
instrumentator = create_instrumentator()

# Instrument the FastAPI application
instrumentator.instrument(app)

# Expose metrics endpoint at /metrics
instrumentator.expose(app, include_in_schema=False, endpoint="/metrics")

# Initialize application info metrics
initialize_application_info(
    version=settings.VERSION if hasattr(settings, "VERSION") else "0.1.0",
    environment=settings.ENVIRONMENT
)

# ============================================================================
# API Router
# ============================================================================

app.include_router(api_router, prefix=settings.API_V1_STR)
