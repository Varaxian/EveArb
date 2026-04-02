from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import User
from app.services.auth_service import get_current_user
from app.services.settings_service import (
    get_platform_region_hub_systems,
    get_platform_tracked_regions,
    get_user_dashboard_filters,
    set_platform_region_hub_systems,
    set_platform_tracked_regions,
    set_user_dashboard_filters,
)

router = APIRouter(prefix="/settings", tags=["settings"])

class PlatformSettingsPayload(BaseModel):
    tracked_regions: list[int]

class HubSystemsPayload(BaseModel):
    region_hub_systems: dict[int, int]

class DashboardFiltersPayload(BaseModel):
    min_roi: float
    min_qty: int
    min_net_profit_isk: float = 0.0
    max_total_m3: float = 0.0
    total_m3_available: float = 0.0
    max_jumps: int = 0
    limit: int = 50
    route_security_mode: str = "any"
    min_system_security: float = 0.0

@router.get("")
def get_settings(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return {
        "current_user_id": current_user.id,
        "tracked_regions": get_platform_tracked_regions(db),
        "region_hub_systems": get_platform_region_hub_systems(db),
        "dashboard_filters": get_user_dashboard_filters(db, current_user.id),
    }

@router.post("/platform")
def save_platform_settings(payload: PlatformSettingsPayload, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    tracked = set_platform_tracked_regions(db, payload.tracked_regions)
    return {"status": "saved", "tracked_regions": tracked}

@router.post("/platform/hubs")
def save_hubs(payload: HubSystemsPayload, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    mapping = set_platform_region_hub_systems(db, payload.region_hub_systems)
    return {"status": "saved", "region_hub_systems": mapping}

@router.post("/filters")
def save_filters(payload: DashboardFiltersPayload, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    filters = set_user_dashboard_filters(db, current_user.id, payload.model_dump())
    return {"status": "saved", "dashboard_filters": filters}
