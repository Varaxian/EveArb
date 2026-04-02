from __future__ import annotations

import json
from sqlalchemy.orm import Session

from app.config import settings
from app.db.models import AppSetting, UserPreference

def _get_app_setting(db: Session, key: str) -> AppSetting | None:
    return db.query(AppSetting).filter(AppSetting.key == key).first()

def _set_app_setting(db: Session, key: str, value: str) -> None:
    row = _get_app_setting(db, key)
    if row is None:
        row = AppSetting(key=key, value=value)
        db.add(row)
    else:
        row.value = value
    db.commit()

def _get_user_pref(db: Session, user_id: int, key: str) -> UserPreference | None:
    return db.query(UserPreference).filter(UserPreference.user_id == user_id, UserPreference.key == key).first()

def _set_user_pref(db: Session, user_id: int, key: str, value: str) -> None:
    row = _get_user_pref(db, user_id, key)
    if row is None:
        row = UserPreference(user_id=user_id, key=key, value=value)
        db.add(row)
    else:
        row.value = value
    db.commit()

def get_platform_tracked_regions(db: Session) -> list[int]:
    row = _get_app_setting(db, "tracked_regions")
    if row and row.value:
        return [int(x) for x in row.value.split(",") if x.strip()]
    return settings.tracked_region_ids()

def set_platform_tracked_regions(db: Session, region_ids: list[int]) -> list[int]:
    clean = sorted(set(int(x) for x in region_ids))
    _set_app_setting(db, "tracked_regions", ",".join(str(x) for x in clean))
    return clean

def get_platform_region_hub_systems(db: Session) -> dict[int, int]:
    row = _get_app_setting(db, "region_hub_systems")
    if row and row.value:
        raw = json.loads(row.value)
        mapping = {int(k): int(v) for k, v in raw.items()}
    else:
        mapping = settings.region_hub_systems()

    # Correct an old bad default that pointed Metropolis at Perimeter instead of Hek.
    if mapping.get(10000042) == 30000144:
        mapping[10000042] = 30002053
        _set_app_setting(db, "region_hub_systems", json.dumps({str(k): v for k, v in mapping.items()}))
    return mapping

def set_platform_region_hub_systems(db: Session, mapping: dict[int, int]) -> dict[int, int]:
    clean = {int(k): int(v) for k, v in mapping.items()}
    _set_app_setting(db, "region_hub_systems", json.dumps({str(k): v for k, v in clean.items()}))
    return clean

def get_numeric_pref(db: Session, user_id: int, key: str, default: float) -> float:
    row = _get_user_pref(db, user_id, key)
    if row and row.value not in (None, ""):
        try:
            return float(row.value)
        except ValueError:
            return default
    return default

def get_text_pref(db: Session, user_id: int, key: str, default: str) -> str:
    row = _get_user_pref(db, user_id, key)
    if row and row.value not in (None, ""):
        return str(row.value)
    return default

def get_user_dashboard_filters(db: Session, user_id: int) -> dict:
    total_m3_available = get_numeric_pref(db, user_id, "filter_total_m3_available", 0.0)
    return {
        "min_roi": get_numeric_pref(db, user_id, "filter_min_roi", settings.min_roi),
        "min_qty": int(get_numeric_pref(db, user_id, "filter_min_qty", settings.min_qty)),
        "min_net_profit_isk": get_numeric_pref(db, user_id, "filter_min_net_profit_isk", 0.0),
        "max_total_m3": get_numeric_pref(db, user_id, "filter_max_total_m3", total_m3_available),
        "total_m3_available": total_m3_available,
        "max_jumps": int(get_numeric_pref(db, user_id, "filter_max_jumps", 0.0)),
        "limit": int(get_numeric_pref(db, user_id, "filter_limit", 50.0)),
        "route_security_mode": get_text_pref(db, user_id, "filter_route_security_mode", "any"),
        "min_system_security": get_numeric_pref(db, user_id, "filter_min_system_security", 0.0),
    }

def set_user_dashboard_filters(db: Session, user_id: int, payload: dict) -> dict:
    total_m3_available = float(payload.get("total_m3_available", 0.0))
    max_total_m3 = float(payload.get("max_total_m3", total_m3_available))
    filters = {
        "min_roi": float(payload.get("min_roi", settings.min_roi)),
        "min_qty": int(payload.get("min_qty", settings.min_qty)),
        "min_net_profit_isk": float(payload.get("min_net_profit_isk", 0.0)),
        "max_total_m3": max_total_m3,
        "total_m3_available": total_m3_available,
        "max_jumps": int(payload.get("max_jumps", 0)),
        "limit": int(payload.get("limit", 50)),
        "route_security_mode": str(payload.get("route_security_mode", "any")),
        "min_system_security": float(payload.get("min_system_security", 0.0)),
    }
    for key, value in filters.items():
        _set_user_pref(db, user_id, f"filter_{key}", str(value))
    return filters
