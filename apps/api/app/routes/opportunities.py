from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import User
from app.services.active_opportunity_service import (
    complete_opportunity,
    fail_opportunity,
    list_user_opportunities,
    save_opportunity,
    serialize_opportunity,
)
from app.services.auth_service import get_current_user

router = APIRouter(prefix="/opportunities", tags=["opportunities"])

class SaveOpportunityPayload(BaseModel):
    type_id: int
    item_name: str | None = None
    src_region_id: int
    dst_region_id: int
    src_best_sell: float | None = None
    dst_best_buy: float | None = None
    buy_price: float | None = None
    sell_price: float | None = None
    buy_location_id: int | None = None
    buy_location_name: str | None = None
    sell_location_id: int | None = None
    sell_location_name: str | None = None
    profit_per_unit: float = 0.0
    net_profit_isk: float = 0.0
    roi: float = 0.0
    max_qty_est: int = 0
    quantity: int | None = None
    volume_m3: float | None = None
    total_m3_necessary: float | None = None
    total_m3: float | None = None
    route_jumps: int | None = None
    route_security_profile: str | None = None

class FailOpportunityPayload(BaseModel):
    fail_reason: str

@router.post('/save')
def save(payload: SaveOpportunityPayload, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    opp = save_opportunity(db, user_id=current_user.id, payload=payload.model_dump())
    return {"status": "saved", "opportunity": serialize_opportunity(opp)}

@router.get('/active')
def active(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = list_user_opportunities(db, user_id=current_user.id)
    return [serialize_opportunity(row) for row in rows]

@router.post('/{opportunity_id}/complete')
def complete(opportunity_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    opp = complete_opportunity(db, user_id=current_user.id, opportunity_id=opportunity_id)
    return {"status": "completed", "opportunity": serialize_opportunity(opp)}

@router.post('/{opportunity_id}/fail')
def fail(opportunity_id: int, payload: FailOpportunityPayload, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    opp = fail_opportunity(db, user_id=current_user.id, opportunity_id=opportunity_id, fail_reason=payload.fail_reason)
    return {"status": "failed", "opportunity": serialize_opportunity(opp)}
