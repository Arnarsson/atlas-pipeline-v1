from fastapi import APIRouter

from app.api.routes import items, login, pipeline, private, quality, users, utils, dashboard, documents, decisions, reports, kpi, audit, demo
from app.core.config import settings

api_router = APIRouter()
api_router.include_router(login.router)
api_router.include_router(users.router)
api_router.include_router(utils.router)
api_router.include_router(items.router)
api_router.include_router(pipeline.router)
api_router.include_router(quality.router)
api_router.include_router(dashboard.router)
api_router.include_router(documents.router)
api_router.include_router(decisions.router)
api_router.include_router(reports.router)
api_router.include_router(kpi.router)
api_router.include_router(audit.router)
api_router.include_router(demo.router)


if settings.ENVIRONMENT == "local":
    api_router.include_router(private.router)
