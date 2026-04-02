from __future__ import annotations

from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.config import settings
from app.db.models import RegionMarketSnapshot
from app.services.esi_universe import get_type_volume_m3
from app.services.location_name_service import resolve_location_names
from app.services.logistics_service import analyze_route, route_passes_security_filters

async def compute_opportunities(
    db: Session,
    *,
    src_region_id: int,
    dst_region_id: int,
    hub_systems: dict[int, int],
    limit: int,
    min_roi: float | None = None,
    min_qty: int | None = None,
    min_net_profit_isk: float | None = None,
    max_total_m3: float | None = None,
    total_m3_available: float | None = None,
    max_jumps: int | None = None,
    route_security_mode: str = "any",
    min_system_security: float = 0.0,
    user_id: int | None = None,
) -> list[dict[str, Any]]:
    src_snapshot = db.query(func.max(RegionMarketSnapshot.snapshot_at)).filter(
        RegionMarketSnapshot.region_id == src_region_id
    ).scalar()
    dst_snapshot = db.query(func.max(RegionMarketSnapshot.snapshot_at)).filter(
        RegionMarketSnapshot.region_id == dst_region_id
    ).scalar()

    if src_snapshot is None or dst_snapshot is None:
        return []

    src_rows = (
        db.query(RegionMarketSnapshot)
        .filter(
            RegionMarketSnapshot.region_id == src_region_id,
            RegionMarketSnapshot.snapshot_at == src_snapshot,
        )
        .all()
    )
    dst_rows = (
        db.query(RegionMarketSnapshot)
        .filter(
            RegionMarketSnapshot.region_id == dst_region_id,
            RegionMarketSnapshot.snapshot_at == dst_snapshot,
        )
        .all()
    )

    src_map = {row.type_id: row for row in src_rows}
    dst_map = {row.type_id: row for row in dst_rows}

    min_roi_value = settings.min_roi if min_roi is None else min_roi
    min_qty_value = settings.min_qty if min_qty is None else min_qty
    min_net_profit_value = 0.0 if min_net_profit_isk is None else min_net_profit_isk
    total_m3_available_value = 0.0 if total_m3_available is None else max(float(total_m3_available), 0.0)
    max_total_m3_value = 0.0 if max_total_m3 is None else max(float(max_total_m3), 0.0)
    if max_total_m3_value <= 0 and total_m3_available_value > 0:
        max_total_m3_value = total_m3_available_value
    max_jumps_value = None if max_jumps is None or max_jumps <= 0 else max_jumps

    route_info = {
        "route_system_ids": [],
        "route_jumps": 0,
        "systems": [],
        "has_highsec": False,
        "has_lowsec": False,
        "has_nullsec": False,
        "security_profile": "any",
        "min_security_on_path": None,
        "max_security_on_path": None,
    }
    if src_region_id in hub_systems and dst_region_id in hub_systems:
        route_info = await analyze_route(db, hub_systems[src_region_id], hub_systems[dst_region_id])

    if max_jumps_value is not None and route_info["route_jumps"] > max_jumps_value:
        return []

    security_values = [row["security_status"] for row in route_info["systems"]]
    if not route_passes_security_filters(
        security_values=security_values,
        route_security_mode=route_security_mode,
        min_system_security=min_system_security,
    ):
        return []

    rough_candidates = []

    for type_id, src in src_map.items():
        dst = dst_map.get(type_id)
        if not dst or src.best_sell is None or dst.best_buy is None:
            continue

        taxes_unit = dst.best_buy * settings.sales_tax_rate
        broker_fees_unit = dst.best_buy * settings.broker_fee_rate
        rough_profit = dst.best_buy - taxes_unit - broker_fees_unit - src.best_sell
        if rough_profit <= 0:
            continue

        qmax = min(int(src.sell_volume or 0), int(dst.buy_volume or 0))
        if qmax < min_qty_value:
            continue

        rough_candidates.append((type_id, src, dst, qmax))

    rough_candidates = rough_candidates[: settings.max_opportunity_rows]

    location_ids: list[int] = []
    for _, src, dst, _ in rough_candidates:
        if src.best_sell_location_id:
            location_ids.append(int(src.best_sell_location_id))
        if dst.best_buy_location_id:
            location_ids.append(int(dst.best_buy_location_id))

    location_names = await resolve_location_names(db, location_ids, settings.esi_user_agent, user_id=user_id)

    results = []
    for type_id, src, dst, qmax in rough_candidates:
        buy_location_id = int(src.best_sell_location_id or 0)
        sell_location_id = int(dst.best_buy_location_id or 0)
        buy_location_name = location_names.get(buy_location_id)
        sell_location_name = location_names.get(sell_location_id)

        if not buy_location_name or not sell_location_name:
            continue

        volume_m3, item_name = await get_type_volume_m3(db, type_id, settings.esi_user_agent)
        total_m3_necessary = volume_m3 * qmax
        fits_cargo = (
            total_m3_available_value > 0
            and total_m3_necessary <= total_m3_available_value
        )

        if max_total_m3_value > 0 and total_m3_necessary > max_total_m3_value:
            continue

        hauling_cost_unit = (settings.cost_per_m3_per_jump * volume_m3 * route_info["route_jumps"]) + (
            settings.base_trip_cost / max(qmax, 1)
        )
        taxes_unit = dst.best_buy * settings.sales_tax_rate
        broker_fees_unit = dst.best_buy * settings.broker_fee_rate
        total_fees_unit = taxes_unit + broker_fees_unit
        profit_per_unit = dst.best_buy - total_fees_unit - src.best_sell - hauling_cost_unit
        if profit_per_unit <= 0:
            continue

        roi = profit_per_unit / max(src.best_sell + hauling_cost_unit, 1e-9)
        if roi < min_roi_value:
            continue

        net_profit_isk = profit_per_unit * qmax
        if net_profit_isk < min_net_profit_value:
            continue

        profit_per_m3 = net_profit_isk / total_m3_necessary if total_m3_necessary > 0 else None
        isk_per_jump = net_profit_isk / route_info["route_jumps"] if route_info["route_jumps"] > 0 else net_profit_isk

        results.append({
            "type_id": type_id,
            "item_name": item_name,
            "src_region_id": src_region_id,
            "dst_region_id": dst_region_id,
            "src_best_sell": src.best_sell,
            "dst_best_buy": dst.best_buy,
            "buy_location_id": buy_location_id,
            "buy_location_name": buy_location_name,
            "sell_location_id": sell_location_id,
            "sell_location_name": sell_location_name,
            "taxes_unit": taxes_unit,
            "broker_fees_unit": broker_fees_unit,
            "total_fees_unit": total_fees_unit,
            "hauling_cost_unit": hauling_cost_unit,
            "profit_per_unit": profit_per_unit,
            "roi": roi,
            "max_qty_est": qmax,
            "route_jumps": route_info["route_jumps"],
            "route_system_ids": route_info["route_system_ids"],
            "route_security_profile": route_info["security_profile"],
            "min_security_on_path": route_info["min_security_on_path"],
            "max_security_on_path": route_info["max_security_on_path"],
            "volume_m3": volume_m3,
            "total_m3": total_m3_necessary,
            "total_m3_necessary": total_m3_necessary,
            "total_m3_available": total_m3_available_value,
            "fits_cargo": fits_cargo,
            "net_profit_isk": net_profit_isk,
            "profit_per_m3": profit_per_m3,
            "isk_per_jump": isk_per_jump,
        })

    results.sort(key=lambda row: row["net_profit_isk"], reverse=True)
    return results[:limit]
