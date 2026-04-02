from __future__ import annotations

import asyncio
from sqlalchemy import func
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException, Query

from app.db.database import get_db
from app.db.models import RegionMarketSnapshot
from app.services.job_service import finish_job, start_job
from app.services.market_service import ingest_regions
from app.services.opportunity_service import compute_opportunities
from app.services.settings_service import get_platform_region_hub_systems, get_platform_tracked_regions
from app.services.auth_service import get_current_user_optional

ALLOWED_ROUTE_SECURITY_MODES = {
    "any",
    "highsec_only",
    "high_low",
    "avoid_null",
    "includes_null",
}

router = APIRouter(prefix="/market", tags=["market"])


@router.post("/ingest")
async def ingest_market(region_ids: str | None = Query(default=None), db: Session = Depends(get_db)):
    target_regions = get_platform_tracked_regions(db)
    if region_ids:
        target_regions = [int(x.strip()) for x in region_ids.split(",") if x.strip()]
    if not target_regions:
        raise HTTPException(status_code=400, detail="No tracked regions configured")

    job = start_job(db, "manual_market_ingest", {"region_ids": target_regions})
    try:
        result = await asyncio.wait_for(ingest_regions(db, target_regions), timeout=120)
        finish_job(db, job.id, "success", result)
        return result
    except asyncio.TimeoutError:
        finish_job(db, job.id, "failed", {"error": "manual ingest timed out after 120 seconds"})
        raise HTTPException(status_code=504, detail="manual ingest timed out after 120 seconds")
    except Exception as exc:
        finish_job(db, job.id, "failed", {"error": repr(exc)})
        raise


@router.get("/latest")
def latest_market(region_id: int = Query(...), limit: int = Query(50, ge=1, le=500), db: Session = Depends(get_db)):
    latest_snapshot = db.query(func.max(RegionMarketSnapshot.snapshot_at)).filter(
        RegionMarketSnapshot.region_id == region_id
    ).scalar()

    if latest_snapshot is None:
        return []

    rows = (
        db.query(RegionMarketSnapshot)
        .filter(
            RegionMarketSnapshot.region_id == region_id,
            RegionMarketSnapshot.snapshot_at == latest_snapshot,
        )
        .order_by(RegionMarketSnapshot.type_id.asc())
        .limit(limit)
        .all()
    )

    return [
        {
            "snapshot_at": row.snapshot_at.isoformat(),
            "region_id": row.region_id,
            "type_id": row.type_id,
            "best_sell": row.best_sell,
            "best_buy": row.best_buy,
            "sell_volume": row.sell_volume,
            "buy_volume": row.buy_volume,
        }
        for row in rows
    ]


@router.get("/opportunities")
async def opportunities(
    src_region_id: int = Query(...),
    dst_region_id: int = Query(...),
    limit: int = Query(50, ge=1, le=500),
    min_roi: float | None = Query(default=None, ge=0.0),
    min_qty: int | None = Query(default=None, ge=1),
    min_net_profit_isk: float | None = Query(default=None, ge=0.0),
    max_total_m3: float | None = Query(default=None, ge=0.0),
    total_m3_available: float | None = Query(default=None, ge=0.0),
    max_jumps: int | None = Query(default=None, ge=0),
    route_security_mode: str = Query(default="any"),
    min_system_security: float = Query(default=0.0),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user_optional),
):
    route_security_mode = (route_security_mode or "any").strip().lower()
    if route_security_mode not in ALLOWED_ROUTE_SECURITY_MODES:
        raise HTTPException(status_code=400, detail="Invalid route_security_mode")

    min_system_security = max(0.0, min(1.0, float(min_system_security or 0.0)))

    hub_systems = get_platform_region_hub_systems(db)
    return await compute_opportunities(
        db,
        src_region_id=src_region_id,
        dst_region_id=dst_region_id,
        hub_systems=hub_systems,
        limit=limit,
        min_roi=min_roi,
        min_qty=min_qty,
        min_net_profit_isk=min_net_profit_isk,
        max_total_m3=max_total_m3,
        total_m3_available=total_m3_available,
        max_jumps=max_jumps,
        route_security_mode=route_security_mode,
        min_system_security=min_system_security,
        user_id=(current_user.id if current_user else None),
    )
