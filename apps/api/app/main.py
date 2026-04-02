from __future__ import annotations

from fastapi import FastAPI

from app.config import settings
from app.routes.auth import router as auth_router

app = FastAPI(title=settings.app_name, version=settings.app_version)

app.include_router(auth_router)

@app.get("/")
def root():
    return {
        "status": "ok",
        "service": "eve-arb-v2.02",
        "auth_routes": ["/auth/login", "/auth/callback"],
    }

@app.get("/health")
def health():
    return {"health": "green", "version": settings.app_version}

@app.get("/config-check")
def config_check():
    return {
        "public_base_url": settings.public_base_url,
        "callback_url": settings.esi_callback_url,
        "client_id_present": bool(settings.esi_client_id),
        "client_secret_present": bool(settings.esi_client_secret),
        "scopes": settings.esi_scopes,
    }
