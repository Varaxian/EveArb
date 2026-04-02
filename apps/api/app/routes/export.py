from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.services.export_service import opportunities_to_csv
from app.services.opportunity_service import compute_opportunities
from app.services.settings_service import get_platform_region_hub_systems, get_platform_tracked_regions
from app.services.auth_service import get_current_user_optional

router = APIRouter(prefix="/export", tags=["export"])


def _normalize_region_filter(value: str | None) -> int | None:
    if value is None:
        return None
    cleaned = str(value).strip().lower()
    if cleaned in {"", "all"}:
        return None
    return int(cleaned)


def _selected_region_ids(db: Session, value: str | None) -> list[int]:
    normalized = _normalize_region_filter(value)
    if normalized is None:
        return get_platform_tracked_regions(db)
    return [normalized]


@router.get("/opportunities.csv")
async def export_opportunities_csv(
    src_region_id: str | None = Query(default="all"),
    dst_region_id: str | None = Query(default="all"),
    limit: int = Query(250, ge=1, le=1000),
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
    hub_systems = get_platform_region_hub_systems(db)
    src_region_ids = _selected_region_ids(db, src_region_id)
    dst_region_ids = _selected_region_ids(db, dst_region_id)
    rows = []
    for src_id in src_region_ids:
        for dst_id in dst_region_ids:
            if src_id == dst_id:
                continue
            rows.extend(await compute_opportunities(
                db,
                src_region_id=src_id,
                dst_region_id=dst_id,
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
            ))
    rows.sort(key=lambda row: row.get("net_profit_isk", 0.0), reverse=True)
    rows = rows[:limit]
    csv_text = opportunities_to_csv(rows)
    return Response(
        content=csv_text,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=opportunities.csv"},
    )
