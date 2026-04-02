from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import settings
from app.db.database import Base, engine, ensure_runtime_schema
from app.routes.app import router as app_router
from app.routes.auth import router as auth_router
from app.routes.export import router as export_router
from app.routes.logistics import router as logistics_router
from app.routes.market import router as market_router
from app.routes.opportunities import router as opportunities_router
from app.routes.scheduler import router as scheduler_router
from app.routes.settings import router as settings_router
from app.routes.ui import router as ui_router
from app.services.scheduler_service import start_scheduler, stop_scheduler

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    ensure_runtime_schema()
    start_scheduler()
    yield
    await stop_scheduler()

app = FastAPI(title=settings.app_name, version="v2.20.05", lifespan=lifespan)

app.include_router(app_router)
app.include_router(auth_router)
app.include_router(settings_router)
app.include_router(market_router)
app.include_router(opportunities_router)
app.include_router(export_router)
app.include_router(logistics_router)
app.include_router(scheduler_router)
app.include_router(ui_router)

@app.get("/")
def root():
    return {
        "status": "ok",
        "service": "eve-arb-v2.20.05",
        "dashboard": "/dashboard",
        "routes": [
            "/health",
            "/config-check",
            "/app/me",
            "/auth/login",
            "/auth/logout",
            "/auth/sessions",
            "/auth/refresh",
            "/settings",
            "/market/ingest",
            "/market/latest",
            "/market/opportunities",
            "/opportunities/save",
            "/opportunities/active",
            "/export/opportunities.csv",
            "/logistics/route",
            "/scheduler/status",
            "/scheduler/run",
            "/dashboard",
            "/active-opportunities",
            "/administrator-settings",
        ],
    }

@app.get("/health")
def health():
    return {"health": "green", "version": "v2.20.05"}

@app.get("/config-check")
def config_check():
    return {
        "public_base_url": settings.public_base_url,
        "callback_url": settings.esi_callback_url,
        "client_id_present": bool(settings.esi_client_id),
        "client_secret_present": bool(settings.esi_client_secret),
        "database_url_present": bool(settings.database_url),
        "tracked_regions_default": settings.tracked_region_ids(),
        "scheduler_enabled": settings.enable_scheduler,
        "scheduler_interval_seconds": settings.scheduler_interval_seconds,
        "broker_fee_rate": settings.broker_fee_rate,
    }
