from fastapi import FastAPI
from app.routes import auth, admin, loads, analytics, refresh, export

app = FastAPI(title="eve_arb_v2.01 API")

@app.get("/health")
async def health() -> dict:
    return {"ok": True, "service": "api", "version": "v2.01"}

app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(admin.router, prefix="/api/v1/admin", tags=["admin"])
app.include_router(loads.router, prefix="/api/v1/loads", tags=["loads"])
app.include_router(analytics.router, prefix="/api/v1/analytics", tags=["analytics"])
app.include_router(refresh.router, prefix="/api/v1/refresh", tags=["refresh"])
app.include_router(export.router, prefix="/api/v1/export", tags=["export"])
