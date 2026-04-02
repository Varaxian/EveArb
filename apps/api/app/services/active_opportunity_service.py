from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.db.models import UserOpportunity

VALID_FAIL_REASONS = {
    "price_changed",
    "order_gone",
    "insufficient_volume",
    "cargo_too_large",
    "route_not_safe",
    "structure_access_denied",
    "competition",
    "insufficient_isk",
    "manual_abort",
    "other",
}

def utcnow() -> datetime:
    return datetime.now(timezone.utc)

def save_opportunity(db: Session, *, user_id: int, payload: dict[str, Any]) -> UserOpportunity:
    opp = UserOpportunity(
        user_id=user_id,
        type_id=int(payload.get("type_id") or 0),
        item_name=payload.get("item_name"),
        src_region_id=int(payload.get("src_region_id") or 0),
        dst_region_id=int(payload.get("dst_region_id") or 0),
        buy_price=float(payload.get("src_best_sell") or payload.get("buy_price") or 0.0),
        sell_price=float(payload.get("dst_best_buy") or payload.get("sell_price") or 0.0),
        buy_location_id=(int(payload["buy_location_id"]) if payload.get("buy_location_id") else None),
        buy_location_name=payload.get("buy_location_name"),
        sell_location_id=(int(payload["sell_location_id"]) if payload.get("sell_location_id") else None),
        sell_location_name=payload.get("sell_location_name"),
        expected_profit_per_unit=float(payload.get("profit_per_unit") or 0.0),
        expected_net_profit_isk=float(payload.get("net_profit_isk") or 0.0),
        roi=float(payload.get("roi") or 0.0),
        quantity=int(payload.get("max_qty_est") or payload.get("quantity") or 0),
        volume_m3=(float(payload["volume_m3"]) if payload.get("volume_m3") is not None else None),
        total_m3=(float(payload["total_m3_necessary"]) if payload.get("total_m3_necessary") is not None else (float(payload["total_m3"]) if payload.get("total_m3") is not None else None)),
        route_jumps=(int(payload["route_jumps"]) if payload.get("route_jumps") is not None else None),
        route_security_profile=payload.get("route_security_profile"),
        status="active",
    )
    db.add(opp)
    db.commit()
    db.refresh(opp)
    return opp

def list_user_opportunities(db: Session, *, user_id: int) -> list[UserOpportunity]:
    return (
        db.query(UserOpportunity)
        .filter(UserOpportunity.user_id == user_id)
        .order_by(UserOpportunity.status.asc(), UserOpportunity.created_at.desc())
        .all()
    )

def complete_opportunity(db: Session, *, user_id: int, opportunity_id: int) -> UserOpportunity:
    opp = db.query(UserOpportunity).filter(UserOpportunity.id == opportunity_id, UserOpportunity.user_id == user_id).first()
    if opp is None:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    opp.status = "completed"
    opp.fail_reason = None
    opp.completed_at = utcnow()
    db.commit()
    db.refresh(opp)
    return opp

def fail_opportunity(db: Session, *, user_id: int, opportunity_id: int, fail_reason: str) -> UserOpportunity:
    opp = db.query(UserOpportunity).filter(UserOpportunity.id == opportunity_id, UserOpportunity.user_id == user_id).first()
    if opp is None:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    fail_reason = (fail_reason or "other").strip().lower()
    if fail_reason not in VALID_FAIL_REASONS:
        raise HTTPException(status_code=400, detail="Invalid fail_reason")
    opp.status = "failed"
    opp.fail_reason = fail_reason
    opp.failed_at = utcnow()
    db.commit()
    db.refresh(opp)
    return opp

def serialize_opportunity(opp: UserOpportunity) -> dict[str, Any]:
    return {
        "id": opp.id,
        "user_id": opp.user_id,
        "type_id": opp.type_id,
        "item_name": opp.item_name,
        "src_region_id": opp.src_region_id,
        "dst_region_id": opp.dst_region_id,
        "buy_price": opp.buy_price,
        "sell_price": opp.sell_price,
        "buy_location_id": opp.buy_location_id,
        "buy_location_name": opp.buy_location_name,
        "sell_location_id": opp.sell_location_id,
        "sell_location_name": opp.sell_location_name,
        "expected_profit_per_unit": opp.expected_profit_per_unit,
        "expected_net_profit_isk": opp.expected_net_profit_isk,
        "roi": opp.roi,
        "quantity": opp.quantity,
        "volume_m3": opp.volume_m3,
        "total_m3": opp.total_m3,
        "route_jumps": opp.route_jumps,
        "route_security_profile": opp.route_security_profile,
        "status": opp.status,
        "fail_reason": opp.fail_reason,
        "created_at": opp.created_at.isoformat() if opp.created_at else None,
        "updated_at": opp.updated_at.isoformat() if opp.updated_at else None,
        "completed_at": opp.completed_at.isoformat() if opp.completed_at else None,
        "failed_at": opp.failed_at.isoformat() if opp.failed_at else None,
    }
